"""Tela de CRUD de parcelamentos (cartão de crédito)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
)

from app.models.installment import Installment
from app.services import cards_service, installments_service
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
        self.ed_nome.setPlaceholderText("Como aparece na fatura")

        self.ed_cartao = QComboBox()
        self.ed_cartao.setEditable(False)
        self._fill_cartoes()

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

        self.form.addRow("Nome na fatura *", self.ed_nome)
        self.form.addRow("Cartão *", self.ed_cartao)
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
            if installment.cartao_id is not None:
                for i in range(self.ed_cartao.count()):
                    if self.ed_cartao.itemData(i) == installment.cartao_id:
                        self.ed_cartao.setCurrentIndex(i)
                        break
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

    def _nova_categoria(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()

    def _fill_cartoes(self) -> None:
        self.ed_cartao.clear()
        self.ed_cartao.addItem("(Selecione o cartão)", None)
        for c in cards_service.list_all():
            self.ed_cartao.addItem(c.nome, c.id)

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
            return False, "Nome na fatura é obrigatório"
        if self.ed_cartao.currentData() is None:
            return False, "Selecione um cartão cadastrado em “Contas e cartões”"
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
        cid = self.ed_cartao.currentData()
        return Installment(
            id=self._installment.id if self._installment else None,
            nome_fatura=self.ed_nome.text().strip(),
            cartao_id=int(cid) if cid is not None else None,
            mes_referencia=mes_ref,
            valor_parcela=float(self.ed_valor_parcela.value()),
            total_parcelas=int(self.ed_total.value()),
            parcelas_pagas=int(self.ed_pagas.value()),
            observacao=self.ed_obs.toPlainText().strip() or None,
            category_id=self._picker_cat.current_category_id(),
        )


class InstallmentsView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Parcelamentos",
            "Controle compras parceladas e acompanhe o saldo devedor.",
            [
                "Nome", "Cartão", "Categoria", "Mês Ref.", "Parcela", "Total",
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
            cnome = i.cartao_nome or "—"
            cat = i.categoria_nome or "—"
            rows.append((i.id or 0, [
                i.nome_fatura,
                cnome,
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
        if not cards_service.list_all():
            QMessageBox.information(
                self,
                "Cadastre um cartão",
                "Cadastre ao menos um cartão em “Contas e cartões” antes de parcelamentos.",
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
