"""Tela de CRUD de pagamentos."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
)

from app.models.payment import Payment
from app.services import accounts_service, payments_service
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency, format_date_br


FORMAS_PAGAMENTO = [
    "Pix",
    "Débito",
    "Crédito",
    "Dinheiro",
    "Boleto",
    "Transferência",
]


class PaymentDialog(FormDialog):
    def __init__(self, parent=None, payment: Optional[Payment] = None) -> None:
        super().__init__(
            "Editar pagamento" if payment else "Novo pagamento", parent
        )
        self._payment = payment

        self.ed_descricao = QLineEdit()
        self.ed_descricao.setPlaceholderText("Ex.: Mercado, Farmácia...")

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 1_000_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(10.0)

        self.ed_data = QDateEdit()
        self.ed_data.setDisplayFormat("dd/MM/yyyy")
        self.ed_data.setCalendarPopup(True)
        self.ed_data.setDate(QDate.currentDate())

        self.ed_conta = QComboBox()
        self.ed_conta.setEditable(False)
        self._fill_contas()

        self.ed_forma = QComboBox()
        self.ed_forma.addItems(FORMAS_PAGAMENTO)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(70)

        self.form.addRow("Descrição *", self.ed_descricao)
        self.form.addRow("Valor *", self.ed_valor)
        self.form.addRow("Data *", self.ed_data)
        self.form.addRow("Conta *", self.ed_conta)
        self.form.addRow("Forma de pagamento *", self.ed_forma)
        self.form.addRow("Observação", self.ed_obs)

        if payment:
            self.ed_descricao.setText(payment.descricao)
            self.ed_valor.setValue(payment.valor)
            self.ed_data.setDate(QDate.fromString(payment.data, "yyyy-MM-dd"))
            if payment.conta_id is not None:
                for i in range(self.ed_conta.count()):
                    if self.ed_conta.itemData(i) == payment.conta_id:
                        self.ed_conta.setCurrentIndex(i)
                        break
            idx = self.ed_forma.findText(payment.forma_pagamento)
            if idx >= 0:
                self.ed_forma.setCurrentIndex(idx)
            self.ed_obs.setPlainText(payment.observacao or "")

    def _fill_contas(self) -> None:
        self.ed_conta.clear()
        self.ed_conta.addItem("(Selecione a conta)", None)
        for a in accounts_service.list_all():
            self.ed_conta.addItem(a.nome, a.id)

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_descricao.text().strip():
            return False, "Descrição é obrigatória"
        if self.ed_valor.value() <= 0:
            return False, "Valor deve ser maior que zero"
        if self.ed_conta.currentData() is None:
            return False, "Selecione uma conta cadastrada em “Contas e cartões”"
        return True, None

    def payload(self) -> Payment:
        cid = self.ed_conta.currentData()
        return Payment(
            id=self._payment.id if self._payment else None,
            valor=float(self.ed_valor.value()),
            descricao=self.ed_descricao.text().strip(),
            data=self.ed_data.date().toString("yyyy-MM-dd"),
            conta_id=int(cid) if cid is not None else None,
            forma_pagamento=self.ed_forma.currentText(),
            observacao=self.ed_obs.toPlainText().strip() or None,
        )


class PaymentsView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Pagamentos",
            "Registre seus gastos avulsos e acompanhe o histórico.",
            ["Data", "Descrição", "Conta", "Forma", "Valor", "Observação"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def reload(self) -> None:
        rows = []
        for p in payments_service.list_all():
            nome = p.conta_nome or "—"
            rows.append((p.id or 0, [
                format_date_br(p.data),
                p.descricao,
                nome,
                p.forma_pagamento,
                format_currency(p.valor),
                p.observacao or "",
            ]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        if not accounts_service.list_all():
            QMessageBox.information(
                self,
                "Cadastre uma conta",
                "Cadastre ao menos uma conta em “Contas e cartões” antes de lançar pagamentos.",
            )
            return
        dlg = PaymentDialog(self)
        if dlg.exec():
            payments_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        pid = self.selected_id()
        if pid is None:
            QMessageBox.information(self, "Editar", "Selecione um pagamento na tabela.")
            return
        payment = payments_service.get(pid)
        if payment is None:
            return
        dlg = PaymentDialog(self, payment)
        if dlg.exec():
            payments_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        pid = self.selected_id()
        if pid is None:
            QMessageBox.information(self, "Excluir", "Selecione um pagamento na tabela.")
            return
        resp = QMessageBox.question(
            self,
            "Excluir pagamento",
            "Deseja realmente excluir este pagamento?",
        )
        if resp == QMessageBox.Yes:
            payments_service.delete(pid)
            self.reload()
            self.data_changed.emit()
