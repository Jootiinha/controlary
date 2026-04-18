"""Cadastro de gastos fixos e controle mensal (pago / pendente)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QDialog,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.fixed_expense import FixedExpense
from app.services import accounts_service, fixed_expenses_service, payments_service
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.card import KpiCard
from app.ui.widgets.category_picker import CategoryPicker
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.ui.widgets.payment_confirmation_dialog import FixedExpensePaidDialog
from app.utils.formatting import format_currency, format_month_br


FORMAS = [
    "Pix", "Débito", "Crédito", "Dinheiro", "Boleto", "Transferência", "Débito Automático",
]


class FixedExpenseDialog(FormDialog):
    def __init__(self, parent=None, fe: Optional[FixedExpense] = None) -> None:
        super().__init__("Editar gasto fixo" if fe else "Novo gasto fixo", parent)
        self._fe = fe

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Aluguel, Luz, Internet, Condomínio")

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 500_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(50.0)

        self.ed_dia = QSpinBox()
        self.ed_dia.setRange(1, 31)
        self.ed_dia.setValue(5)

        self.cmb_conta = QComboBox()
        self.cmb_conta.setEditable(False)
        self._fill_contas()

        self.cmb_forma = QComboBox()
        self.cmb_forma.addItems(FORMAS)

        self._picker_cat = CategoryPicker(self, allow_empty=False)
        self._picker_cat.connect_new_button(self._nova_categoria)

        self.chk_ativo = QCheckBox("Ativo (entra nas projeções)")
        self.chk_ativo.setChecked(True)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Valor mensal *", self.ed_valor)
        self.form.addRow("Dia de vencimento *", self.ed_dia)
        self.form.addRow("Conta", self.cmb_conta)
        self.form.addRow("Categoria *", self._picker_cat)
        self.form.addRow("Forma de pagamento *", self.cmb_forma)
        self.form.addRow("", self.chk_ativo)
        self.form.addRow("Observação", self.ed_obs)

        if fe:
            self.ed_nome.setText(fe.nome)
            self.ed_valor.setValue(fe.valor_mensal)
            self.ed_dia.setValue(fe.dia_referencia)
            if fe.conta_id is not None:
                for i in range(self.cmb_conta.count()):
                    if self.cmb_conta.itemData(i) == fe.conta_id:
                        self.cmb_conta.setCurrentIndex(i)
                        break
            idx = self.cmb_forma.findText(fe.forma_pagamento)
            if idx >= 0:
                self.cmb_forma.setCurrentIndex(idx)
            self.chk_ativo.setChecked(fe.ativo)
            self.ed_obs.setPlainText(fe.observacao or "")
            if fe.category_id is not None:
                self._picker_cat.set_category_id(fe.category_id)

    def _nova_categoria(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()

    def _fill_contas(self) -> None:
        self.cmb_conta.clear()
        self.cmb_conta.addItem("(Nenhuma)", None)
        for a in accounts_service.list_all():
            self.cmb_conta.addItem(a.nome, a.id)

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Informe o nome"
        if self.ed_valor.value() <= 0:
            return False, "Valor deve ser maior que zero"
        if self._picker_cat.current_category_id() is None:
            return False, "Selecione uma categoria"
        return True, None

    def payload(self) -> FixedExpense:
        cid = self.cmb_conta.currentData()
        return FixedExpense(
            id=self._fe.id if self._fe else None,
            nome=self.ed_nome.text().strip(),
            valor_mensal=float(self.ed_valor.value()),
            dia_referencia=int(self.ed_dia.value()),
            forma_pagamento=self.cmb_forma.currentText(),
            conta_id=int(cid) if cid is not None else None,
            observacao=self.ed_obs.toPlainText().strip() or None,
            ativo=self.chk_ativo.isChecked(),
            category_id=self._picker_cat.current_category_id(),
        )


class _FixedCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Itens de gasto fixo",
            "Aluguel, contas de consumo, telefone etc. O valor entra no previsto até marcar como pago no mês.",
            ["Nome", "Valor/mês", "Dia", "Conta", "Categoria", "Forma", "Ativo"],
        )
        self._by_id: dict[int, FixedExpense] = {}
        self.totals_wrap.setVisible(True)
        self._kp_mensal = KpiCard("Total mensal (ativos)", "-", compact=True)
        self._kp_ativos = KpiCard("Ativos", "-", compact=True)
        self._kp_cad = KpiCard("Cadastrados", "-", compact=True)
        self.totals_bar.addWidget(self._kp_mensal)
        self.totals_bar.addWidget(self._kp_ativos)
        self.totals_bar.addWidget(self._kp_cad)
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)

    def _refresh_kpi_cards(self) -> None:
        ativos = [fe for fe in self._by_id.values() if fe.ativo]
        total_m = sum(fe.valor_mensal for fe in ativos)
        self._kp_mensal.set_value(format_currency(total_m))
        self._kp_ativos.set_value(str(len(ativos)))
        self._kp_cad.set_value(str(len(self._by_id)))

    def reload(self) -> None:
        self._by_id.clear()
        rows = []
        for fe in fixed_expenses_service.list_all():
            if fe.id is not None:
                self._by_id[fe.id] = fe
            cat = fe.categoria_nome or "—"
            rows.append((fe.id or 0, [
                fe.nome,
                format_currency(fe.valor_mensal),
                str(fe.dia_referencia),
                fe.conta_nome or "—",
                cat,
                fe.forma_pagamento,
                "Sim" if fe.ativo else "Não",
            ]))
        self.model.set_rows(rows)
        self._refresh_kpi_cards()
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        if not self._by_id:
            self.set_footer_text("", "")
            return
        vis = [self._by_id[i] for i in visible_ids if i in self._by_id]
        total = sum(fe.valor_mensal for fe in vis)
        self.set_footer_text(
            f"Total mensal (visíveis): {format_currency(total)}",
            f"Itens: {len(vis)}",
        )

    def _add(self) -> None:
        dlg = FixedExpenseDialog(self)
        if dlg.exec():
            fixed_expenses_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        fid = self.selected_id()
        if fid is None:
            QMessageBox.information(self, "Editar", "Selecione um item.")
            return
        fe = fixed_expenses_service.get(fid)
        if fe is None:
            return
        dlg = FixedExpenseDialog(self, fe)
        if dlg.exec():
            fixed_expenses_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        fid = self.selected_id()
        if fid is None:
            QMessageBox.information(self, "Excluir", "Selecione um item.")
            return
        if QMessageBox.question(self, "Excluir", "Excluir este gasto fixo?") != QMessageBox.Yes:
            return
        fixed_expenses_service.delete(fid)
        self.reload()
        self.data_changed.emit()


class _MonthlyControl(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[tuple[int, QComboBox]] = []
        self._monthly_hints: list[str] = []

        hint = QLabel(
            "Escolha a competência (mês/ano). Cada item ativo aparece como Pendente até você marcar Pago. "
            "O previsto do mês e o total do restante do ano usam só o que ainda está pendente."
        )
        hint.setWordWrap(True)
        hint.setObjectName("PageSubtitle")

        row = QHBoxLayout()
        row.addWidget(QLabel("Competência:"))
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        self.dt.dateChanged.connect(self._reload_table)
        row.addWidget(self.dt)
        row.addStretch()
        self.btn_edit = QPushButton("Editar despesa…")
        self.btn_edit.setObjectName("PrimaryButton")
        self.btn_edit.setToolTip(
            "Abre o cadastro do gasto fixo selecionado. "
            "Também é possível dar duplo clique em Nome, Valor, Dia ou Observação."
        )
        self.btn_edit.clicked.connect(self._edit_selected)
        row.addWidget(self.btn_edit)

        kpi_row = QHBoxLayout()
        self._kp_pago = KpiCard("Pago no mês", "-", compact=True)
        self._kp_pend = KpiCard("Pendente no mês", "-", compact=True)
        self._kp_mes = KpiCard("Total do mês", "-", compact=True)
        kpi_row.addWidget(self._kp_pago)
        kpi_row.addWidget(self._kp_pend)
        kpi_row.addWidget(self._kp_mes)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Buscar:"))
        self._monthly_search = QLineEdit()
        self._monthly_search.setPlaceholderText("Buscar…")
        self._monthly_search.setClearButtonEnabled(True)
        self._monthly_search.textChanged.connect(self._apply_monthly_search)
        search_row.addWidget(self._monthly_search, 1)

        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(
            ["Nome", "Valor", "Dia", "Status", "Observação"]
        )
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.verticalHeader().setDefaultSectionSize(44)
        self.tbl.setWordWrap(False)

        th = self.tbl.horizontalHeader()
        th.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        th.setStretchLastSection(False)
        th.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        th.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        th.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        th.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        th.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tbl.setColumnWidth(1, 112)
        self.tbl.setColumnWidth(2, 44)
        self.tbl.setColumnWidth(3, 178)

        self.tbl.cellDoubleClicked.connect(self._on_cell_double_clicked)

        proj_title = QLabel("Projeção — meses restantes do ano (só pendentes)")
        proj_title.setObjectName("PageSubtitle")
        self.tbl_proj = QTableWidget(0, 2)
        self.tbl_proj.setHorizontalHeaderLabels(["Mês", "Total pendente (fixos)"])
        self.tbl_proj.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_proj.setSelectionMode(QAbstractItemView.NoSelection)
        self.tbl_proj.verticalHeader().setVisible(False)
        self.tbl_proj.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.tbl_proj.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.tbl_proj.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(hint)
        layout.addLayout(row)
        layout.addLayout(kpi_row)
        layout.addLayout(search_row)
        layout.addWidget(self.tbl, 1)
        layout.addWidget(proj_title)
        layout.addWidget(self.tbl_proj, 1)
        self._reload_table()
        self._reload_projection()

    def ano_mes(self) -> str:
        d = self.dt.date()
        return f"{d.year():04d}-{d.month():02d}"

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        if col == 3:
            return
        self._edit_row(row)

    def _edit_selected(self) -> None:
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Editar", "Selecione uma linha na tabela (clique no nome ou em outra coluna)."
            )
            return
        self._edit_row(row)

    def _refresh_monthly_kpis(self) -> None:
        ym = self.ano_mes()
        pago = 0.0
        pend = 0.0
        for fe in fixed_expenses_service.list_active():
            if fe.id is None:
                continue
            v = float(fe.valor_mensal)
            if fixed_expenses_service.is_paid(fe.id, ym):
                pago += v
            else:
                pend += v
        total = pago + pend
        self._kp_pago.set_value(format_currency(pago))
        self._kp_pend.set_value(format_currency(pend))
        self._kp_mes.set_value(format_currency(total))

    def _apply_monthly_search(self) -> None:
        needle = self._monthly_search.text().strip().lower()
        for i in range(self.tbl.rowCount()):
            if i >= len(self._monthly_hints):
                continue
            if not needle:
                self.tbl.setRowHidden(i, False)
            else:
                self.tbl.setRowHidden(i, needle not in self._monthly_hints[i])

    def _edit_row(self, row: int) -> None:
        if row < 0 or row >= len(self._rows):
            return
        fid = self._rows[row][0]
        fe = fixed_expenses_service.get(fid)
        if fe is None:
            return
        dlg = FixedExpenseDialog(self, fe)
        if dlg.exec():
            fixed_expenses_service.update(dlg.payload())
            self.data_changed.emit()
            self._reload_table()
            self._reload_projection()

    def _reload_table(self) -> None:
        self._rows.clear()
        self._monthly_hints.clear()
        ym = self.ano_mes()
        items = fixed_expenses_service.list_active()
        self.tbl.setRowCount(len(items))
        align_left = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        align_val = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        align_center = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter
        for i, fe in enumerate(items):
            if fe.id is None:
                continue

            it_nome = QTableWidgetItem(fe.nome)
            it_nome.setTextAlignment(align_left)
            self.tbl.setItem(i, 0, it_nome)

            it_val = QTableWidgetItem(format_currency(fe.valor_mensal))
            it_val.setTextAlignment(align_val)
            self.tbl.setItem(i, 1, it_val)

            it_dia = QTableWidgetItem(str(fe.dia_referencia))
            it_dia.setTextAlignment(align_center)
            self.tbl.setItem(i, 2, it_dia)

            it_obs = QTableWidgetItem(fe.observacao or "")
            it_obs.setTextAlignment(align_left)
            self.tbl.setItem(i, 4, it_obs)

            cb = QComboBox()
            cb.addItems(["Pendente", "Pago"])
            cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cb.setMinimumWidth(138)
            pago = fixed_expenses_service.is_paid(fe.id, ym)
            cb.blockSignals(True)
            cb.setCurrentIndex(1 if pago else 0)
            cb.blockSignals(False)
            fid = fe.id

            def make_handler(f_id: int, combo: QComboBox, competencia: str):
                def on_change(_idx: int) -> None:
                    want_pago = combo.currentIndex() == 1
                    was_pago = fixed_expenses_service.is_paid(f_id, competencia)
                    if want_pago and not was_pago:
                        fe = fixed_expenses_service.get(f_id)
                        if fe is None:
                            return
                        dlg = FixedExpensePaidDialog(self, fe, competencia)
                        if dlg.exec() != QDialog.Accepted:
                            combo.blockSignals(True)
                            combo.setCurrentIndex(0)
                            combo.blockSignals(False)
                            return
                        mp = dlg.mirror_payment()
                        if mp is not None:
                            payments_service.create(mp)
                        fixed_expenses_service.set_month_status(
                            f_id, competencia, pago=True
                        )
                    else:
                        fixed_expenses_service.set_month_status(
                            f_id, competencia, pago=want_pago
                        )
                    self.data_changed.emit()
                    self._reload_projection()
                    self._refresh_monthly_kpis()

                return on_change

            cb.currentIndexChanged.connect(make_handler(fid, cb, ym))

            status_cell = QWidget()
            status_lay = QHBoxLayout(status_cell)
            status_lay.setContentsMargins(6, 2, 6, 2)
            status_lay.setSpacing(0)
            status_lay.addWidget(cb, 1, Qt.AlignmentFlag.AlignVCenter)
            self.tbl.setCellWidget(i, 3, status_cell)
            self._rows.append((fid, cb))

            st_txt = "pago" if pago else "pendente"
            hint = " ".join(
                [
                    fe.nome.lower(),
                    format_currency(fe.valor_mensal).lower(),
                    str(fe.dia_referencia),
                    st_txt,
                    (fe.observacao or "").lower(),
                ]
            )
            self._monthly_hints.append(hint)

        self._refresh_monthly_kpis()
        self._apply_monthly_search()

    def _reload_projection(self) -> None:
        data = fixed_expenses_service.projection_by_month_rest_of_year()
        self.tbl_proj.setRowCount(len(data))
        for i, (ym, total) in enumerate(data):
            self.tbl_proj.setItem(i, 0, QTableWidgetItem(format_month_br(ym)))
            self.tbl_proj.setItem(i, 1, QTableWidgetItem(format_currency(total)))

    def reload_all(self) -> None:
        self._reload_table()
        self._reload_projection()


class FixedExpensesView(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._crud = _FixedCrud()
        self._month = _MonthlyControl()
        self._crud.data_changed.connect(self.data_changed.emit)
        self._month.data_changed.connect(self.data_changed.emit)

        tabs = QTabWidget()
        tabs.addTab(self._crud, "Cadastro")
        tabs.addTab(self._month, "Situação mensal")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs, 1)

    def reload(self) -> None:
        self._crud.reload()
        self._month.reload_all()
