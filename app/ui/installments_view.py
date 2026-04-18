"""Tela de CRUD de parcelamentos (cartão ou conta corrente)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.installment import Installment
from app.services import (
    accounts_service,
    cards_service,
    installment_months_service,
    installments_service,
)
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.card import KpiCard
from app.ui.widgets.category_picker import CategoryPicker
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency, format_month_br


class InstallmentDialog(FormDialog):
    def __init__(self, parent=None, installment: Optional[Installment] = None) -> None:
        super().__init__(
            "Editar parcelamento" if installment else "Novo parcelamento", parent
        )
        self._installment = installment

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Como aparece na fatura ou descrição")

        self.ed_origem = QComboBox()
        self.ed_origem.setEditable(False)
        self._fill_origem()

        self._picker_cat = CategoryPicker(self, allow_empty=False)
        self._picker_cat.connect_new_button(self._nova_categoria)

        self.ed_mes = QDateEdit()
        self.ed_mes.setDisplayFormat("MM/yyyy")
        self.ed_mes.setCalendarPopup(True)
        self.ed_mes.setDate(QDate.currentDate())

        self.ed_valor_parcela = QDoubleSpinBox()
        self.ed_valor_parcela.setRange(0.0, 1_000_000.0)
        self.ed_valor_parcela.setDecimals(2)
        self.ed_valor_parcela.setPrefix("R$ ")
        self.ed_valor_parcela.setSingleStep(10.0)

        self.ed_total = QSpinBox()
        self.ed_total.setRange(1, 360)
        self.ed_total.setValue(12)

        self.ed_pagas = QSpinBox()
        self.ed_pagas.setRange(0, 360)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(70)

        self.lbl_calc = QLabel()
        self.lbl_calc.setStyleSheet("color: #6B7280;")

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Cartão ou conta *", self.ed_origem)
        self.form.addRow("Categoria *", self._picker_cat)
        self.form.addRow("Mês de referência *", self.ed_mes)
        self.form.addRow("Valor da parcela *", self.ed_valor_parcela)
        self.form.addRow("Total de parcelas *", self.ed_total)
        self.form.addRow("Parcelas pagas", self.ed_pagas)
        self.form.addRow("Resumo", self.lbl_calc)
        self.form.addRow("Observação", self.ed_obs)

        self.ed_valor_parcela.valueChanged.connect(self._update_calc)
        self.ed_total.valueChanged.connect(self._update_calc)
        self.ed_pagas.valueChanged.connect(self._update_calc)

        if installment:
            self.ed_nome.setText(installment.nome_fatura)
            self._select_origem(installment)
            try:
                year, month = installment.mes_referencia.split("-")
                self.ed_mes.setDate(QDate(int(year), int(month), 1))
            except Exception:
                pass
            self.ed_valor_parcela.setValue(installment.valor_parcela)
            self.ed_total.setValue(installment.total_parcelas)
            self.ed_pagas.setValue(installment.parcelas_pagas)
            self.ed_obs.setPlainText(installment.observacao or "")
            if installment.category_id is not None:
                self._picker_cat.set_category_id(installment.category_id)

        self._update_calc()

    def _select_origem(self, inst: Installment) -> None:
        for i in range(self.ed_origem.count()):
            data = self.ed_origem.itemData(i)
            if not data or not isinstance(data, str):
                continue
            kind, _, mid = data.partition(":")
            if not mid.isdigit():
                continue
            iid = int(mid)
            if inst.cartao_id is not None and kind == "c" and iid == inst.cartao_id:
                self.ed_origem.setCurrentIndex(i)
                return
            if inst.account_id is not None and kind == "a" and iid == inst.account_id:
                self.ed_origem.setCurrentIndex(i)
                return

    def _nova_categoria(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()

    def _fill_origem(self) -> None:
        self.ed_origem.clear()
        self.ed_origem.addItem("(Selecione cartão ou conta)", None)
        for c in cards_service.list_all():
            if c.id is not None:
                self.ed_origem.addItem(f"Cartão · {c.nome}", f"c:{c.id}")
        for a in accounts_service.list_all():
            if a.id is not None:
                self.ed_origem.addItem(f"Conta · {a.nome}", f"a:{a.id}")

    def _update_calc(self) -> None:
        total = self.ed_total.value()
        pagas = self.ed_pagas.value()
        if pagas > total:
            self.ed_pagas.setValue(total)
            pagas = total
        valor = self.ed_valor_parcela.value()
        restantes = total - pagas
        valor_total = valor * total
        saldo = valor * restantes
        status = "quitado" if pagas >= total else "ativo"
        self.lbl_calc.setText(
            f"Total: {format_currency(valor_total)}  ·  "
            f"Restantes: {restantes}  ·  "
            f"Saldo devedor: {format_currency(saldo)}  ·  "
            f"Status: {status}"
        )

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.ed_origem.currentData() is None:
            return False, "Selecione cartão ou conta em “Contas e cartões”"
        if self.ed_valor_parcela.value() <= 0:
            return False, "Valor da parcela deve ser maior que zero"
        if self.ed_pagas.value() > self.ed_total.value():
            return False, "Parcelas pagas não pode exceder o total"
        if self._picker_cat.current_category_id() is None:
            return False, "Selecione uma categoria"
        return True, None

    def payload(self) -> Installment:
        date_q = self.ed_mes.date()
        mes_ref = f"{date_q.year():04d}-{date_q.month():02d}"
        raw = self.ed_origem.currentData()
        cartao_id: Optional[int] = None
        account_id: Optional[int] = None
        if raw and isinstance(raw, str):
            kind, _, mid = raw.partition(":")
            if mid.isdigit():
                if kind == "c":
                    cartao_id = int(mid)
                elif kind == "a":
                    account_id = int(mid)
        return Installment(
            id=self._installment.id if self._installment else None,
            nome_fatura=self.ed_nome.text().strip(),
            cartao_id=cartao_id,
            account_id=account_id,
            mes_referencia=mes_ref,
            valor_parcela=float(self.ed_valor_parcela.value()),
            total_parcelas=int(self.ed_total.value()),
            parcelas_pagas=int(self.ed_pagas.value()),
            observacao=self.ed_obs.toPlainText().strip() or None,
            category_id=self._picker_cat.current_category_id(),
        )


class _InstallmentsCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Parcelamentos",
            "Controle compras parceladas no cartão ou à vista na conta.",
            [
                "Nome", "Meio", "Categoria", "Mês Ref.", "Parcela", "Total",
                "Pagas", "Restantes", "Saldo devedor", "Status",
            ],
        )
        self._by_id: dict[int, Installment] = {}
        self.totals_wrap.setVisible(True)
        self._kp_saldo = KpiCard("Saldo devedor (ativos)", "-", compact=True)
        self._kp_parcela = KpiCard("Parcela mensal (ativos)", "-", compact=True)
        self._kp_ativos = KpiCard("Ativos", "-", compact=True)
        self._kp_quit = KpiCard("Quitados", "-", compact=True)
        self.totals_bar.addWidget(self._kp_saldo)
        self.totals_bar.addWidget(self._kp_parcela)
        self.totals_bar.addWidget(self._kp_ativos)
        self.totals_bar.addWidget(self._kp_quit)
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def _refresh_kpi_cards(self) -> None:
        ativos = [i for i in self._by_id.values() if i.status == "ativo"]
        quitados = [i for i in self._by_id.values() if i.status != "ativo"]
        saldo = sum(i.saldo_devedor for i in ativos)
        parc_m = sum(i.valor_parcela for i in ativos)
        self._kp_saldo.set_value(format_currency(saldo))
        self._kp_parcela.set_value(format_currency(parc_m))
        self._kp_ativos.set_value(str(len(ativos)))
        self._kp_quit.set_value(str(len(quitados)))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for i in installments_service.list_all():
            if i.id is not None:
                self._by_id[i.id] = i
            meio = i.meio_label
            cat = i.categoria_nome or "—"
            rows.append((i.id or 0, [
                i.nome_fatura,
                meio,
                cat,
                format_month_br(i.mes_referencia),
                format_currency(i.valor_parcela),
                format_currency(i.valor_total),
                f"{i.parcelas_pagas}/{i.total_parcelas}",
                str(i.parcelas_restantes),
                format_currency(i.saldo_devedor),
                i.status.capitalize(),
            ]))
        self.model.set_rows(rows)
        self._refresh_kpi_cards()
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        if not self._by_id:
            self.set_footer_text("", "")
            return
        vis = [self._by_id[i] for i in visible_ids if i in self._by_id]
        saldo = sum(i.saldo_devedor for i in vis)
        rest = sum(i.parcelas_restantes for i in vis)
        self.set_footer_text(
            f"Saldo devedor (visíveis): {format_currency(saldo)}",
            f"Parcelas restantes (visíveis): {rest}",
        )

    def _add(self) -> None:
        if not cards_service.list_all() and not accounts_service.list_all():
            QMessageBox.information(
                self,
                "Cadastre cartão ou conta",
                "Cadastre ao menos um cartão ou uma conta em “Contas e cartões”.",
            )
            return
        dlg = InstallmentDialog(self)
        if dlg.exec():
            installments_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        iid = self.selected_id()
        if iid is None:
            QMessageBox.information(self, "Editar", "Selecione um parcelamento.")
            return
        inst = installments_service.get(iid)
        if inst is None:
            return
        dlg = InstallmentDialog(self, inst)
        if dlg.exec():
            installments_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        iid = self.selected_id()
        if iid is None:
            QMessageBox.information(self, "Excluir", "Selecione um parcelamento.")
            return
        resp = QMessageBox.question(
            self, "Excluir",
            "Excluir este parcelamento? O histórico será perdido."
        )
        if resp == QMessageBox.Yes:
            installments_service.delete(iid)
            self.reload()
            self.data_changed.emit()


class _InstallmentMonthlyControl(QWidget):
    """Parcelas em conta na competência do mês de referência."""
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        hint = QLabel(
            "Parcelamentos à vista na conta cujo mês de referência coincide com a competência. "
            "Marque Pago quando debitar a parcela."
        )
        hint.setWordWrap(True)
        hint.setObjectName("PageSubtitle")
        row = QHBoxLayout()
        row.addWidget(QLabel("Competência:"))
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        self.dt.dateChanged.connect(self.reload_table)
        row.addWidget(self.dt)
        row.addStretch()
        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(
            ["Nome", "Valor parcela", "Conta", "Mês ref.", "Situação no mês"]
        )
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionMode(QAbstractItemView.NoSelection)
        self.tbl.verticalHeader().setVisible(False)
        lay = QVBoxLayout(self)
        lay.addWidget(hint)
        lay.addLayout(row)
        lay.addWidget(self.tbl, 1)
        self.reload_table()

    def ano_mes(self) -> str:
        d = self.dt.date()
        return f"{d.year():04d}-{d.month():02d}"

    def reload_table(self) -> None:
        ym = self.ano_mes()
        items = [
            i
            for i in installments_service.list_all()
            if i.status == "ativo"
            and i.account_id is not None
            and i.cartao_id is None
            and i.mes_referencia == ym
            and i.id is not None
        ]
        self.tbl.setRowCount(len(items))
        align_left = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        align_val = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        for i, inst in enumerate(items):
            assert inst.id is not None
            iid = inst.id
            it_n = QTableWidgetItem(inst.nome_fatura)
            it_n.setTextAlignment(align_left)
            self.tbl.setItem(i, 0, it_n)
            it_v = QTableWidgetItem(format_currency(inst.valor_parcela))
            it_v.setTextAlignment(align_val)
            self.tbl.setItem(i, 1, it_v)
            acc = accounts_service.get(int(inst.account_id))
            it_c = QTableWidgetItem(acc.nome if acc else "—")
            it_c.setTextAlignment(align_left)
            self.tbl.setItem(i, 2, it_c)
            it_m = QTableWidgetItem(format_month_br(inst.mes_referencia))
            it_m.setTextAlignment(align_left)
            self.tbl.setItem(i, 3, it_m)
            cb = QComboBox()
            cb.addItems(["Pendente", "Pago"])
            pago = installment_months_service.is_paid(iid, ym)
            cb.blockSignals(True)
            cb.setCurrentIndex(1 if pago else 0)
            cb.blockSignals(False)
            cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            def make_handler(inst_id: int, combo: QComboBox, competencia: str):
                def on_change(_idx: int) -> None:
                    want = combo.currentIndex() == 1
                    installment_months_service.set_month_status(
                        inst_id, competencia, pago=want
                    )
                    self.data_changed.emit()

                return on_change

            cb.currentIndexChanged.connect(make_handler(iid, cb, ym))
            self.tbl.setCellWidget(i, 4, cb)


class InstallmentsView(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._crud = _InstallmentsCrud()
        self._month = _InstallmentMonthlyControl()
        self._crud.data_changed.connect(self.data_changed.emit)
        self._month.data_changed.connect(self.data_changed.emit)
        tabs = QTabWidget()
        tabs.addTab(self._crud, "Cadastro")
        tabs.addTab(self._month, "Situação mensal (conta)")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(tabs)

    def reload(self) -> None:
        self._crud.reload()
        self._month.reload_table()
