"""Tela de CRUD de pagamentos."""
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
)

from app.models.payment import Payment
from app.services import accounts_service, cards_service, payments_service
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.category_picker import CategoryPicker
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.payment_confirmation_dialog import PaymentRecordedDialog
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

        self.cmb_origem = QComboBox()
        self.cmb_origem.setEditable(False)
        self._fill_origem()

        self.lbl_origem = QLabel("")
        self.lbl_origem.setWordWrap(True)
        self.lbl_origem.setStyleSheet("color: #6B7280;")

        self._picker_cat = CategoryPicker(self, allow_empty=False)
        self._picker_cat.connect_new_button(self._nova_categoria)

        self.ed_forma = QComboBox()
        self.ed_forma.addItems(FORMAS_PAGAMENTO)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(70)

        self.form.addRow("Descrição *", self.ed_descricao)
        self.form.addRow("Valor *", self.ed_valor)
        self.form.addRow("Data *", self.ed_data)
        self.form.addRow("Origem *", self.cmb_origem)
        self.form.addRow("", self.lbl_origem)
        self.form.addRow("Categoria *", self._picker_cat)
        self.form.addRow("Forma de pagamento *", self.ed_forma)
        self.form.addRow("Observação", self.ed_obs)

        self.cmb_origem.currentIndexChanged.connect(lambda _: self._sync_origem())

        if payment:
            self.ed_descricao.setText(payment.descricao)
            self.ed_valor.setValue(payment.valor)
            self.ed_data.setDate(QDate.fromString(payment.data, "yyyy-MM-dd"))
            if payment.conta_id is not None:
                for i in range(self.cmb_origem.count()):
                    d = self.cmb_origem.itemData(i)
                    if d == f"acc:{payment.conta_id}":
                        self.cmb_origem.setCurrentIndex(i)
                        break
            elif payment.cartao_id is not None:
                for i in range(self.cmb_origem.count()):
                    d = self.cmb_origem.itemData(i)
                    if d == f"card:{payment.cartao_id}":
                        self.cmb_origem.setCurrentIndex(i)
                        break
            idx = self.ed_forma.findText(payment.forma_pagamento)
            if idx >= 0:
                self.ed_forma.setCurrentIndex(idx)
            self.ed_obs.setPlainText(payment.observacao or "")
            if payment.category_id is not None:
                self._picker_cat.set_category_id(payment.category_id)

        self._sync_origem()

    def _sync_origem(self) -> None:
        raw = self.cmb_origem.currentData()
        if not raw or not isinstance(raw, str):
            self.lbl_origem.clear()
            self.ed_forma.setEnabled(True)
            return
        kind, _, mid = raw.partition(":")
        if kind == "card" and mid:
            self.ed_forma.setEnabled(False)
            idx = self.ed_forma.findText("Crédito")
            if idx >= 0:
                self.ed_forma.setCurrentIndex(idx)
            try:
                cid = int(mid)
            except ValueError:
                self.lbl_origem.clear()
                return
            c = cards_service.get(cid)
            if c:
                self.lbl_origem.setText(
                    f"Lançamento na fatura do cartão (competência pelo mês da data)."
                )
            else:
                self.lbl_origem.clear()
        else:
            self.lbl_origem.clear()
            self.ed_forma.setEnabled(True)

    def _nova_categoria(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            from app.services import categories_service

            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()

    def _fill_origem(self) -> None:
        self.cmb_origem.clear()
        self.cmb_origem.addItem("(Selecione conta ou cartão)", None)
        for a in accounts_service.list_all():
            self.cmb_origem.addItem(f"Conta · {a.nome}", f"acc:{a.id}")
        for c in cards_service.list_all():
            self.cmb_origem.addItem(f"Cartão · {c.nome}", f"card:{c.id}")

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_descricao.text().strip():
            return False, "Descrição é obrigatória"
        if self.ed_valor.value() <= 0:
            return False, "Valor deve ser maior que zero"
        if self.cmb_origem.currentData() is None:
            return False, "Selecione conta bancária ou cartão em “Contas e cartões”"
        if self._picker_cat.current_category_id() is None:
            return False, "Selecione uma categoria"
        return True, None

    def payload(self) -> Payment:
        account_id: Optional[int] = None
        card_id: Optional[int] = None
        raw = self.cmb_origem.currentData()
        if raw and isinstance(raw, str):
            kind, _, mid = raw.partition(":")
            if mid:
                try:
                    iid = int(mid)
                except ValueError:
                    iid = None
                if iid is not None:
                    if kind == "acc":
                        account_id = iid
                    elif kind == "card":
                        card_id = iid
        forma = "Crédito" if card_id is not None else self.ed_forma.currentText()
        return Payment(
            id=self._payment.id if self._payment else None,
            valor=float(self.ed_valor.value()),
            descricao=self.ed_descricao.text().strip(),
            data=self.ed_data.date().toString("yyyy-MM-dd"),
            conta_id=account_id,
            cartao_id=card_id,
            forma_pagamento=forma,
            observacao=self.ed_obs.toPlainText().strip() or None,
            category_id=self._picker_cat.current_category_id(),
        )


class PaymentsView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Pagamentos",
            "Registre seus gastos avulsos e acompanhe o histórico.",
            ["Data", "Descrição", "Origem", "Categoria", "Forma", "Valor", "Observação"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def reload(self) -> None:
        rows = []
        for p in payments_service.list_all():
            nome = p.conta_nome or p.cartao_nome or "—"
            cat = p.categoria_nome or "—"
            rows.append((p.id or 0, [
                format_date_br(p.data),
                p.descricao,
                nome,
                cat,
                p.forma_pagamento,
                format_currency(p.valor),
                p.observacao or "",
            ]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        if not accounts_service.list_all() and not cards_service.list_all():
            QMessageBox.information(
                self,
                "Cadastre uma origem",
                "Cadastre ao menos uma conta ou cartão em “Contas e cartões”.",
            )
            return
        dlg = PaymentDialog(self)
        if dlg.exec():
            pay = dlg.payload()
            payments_service.create(pay)
            origem = "—"
            if pay.conta_id is not None:
                a = accounts_service.get(pay.conta_id)
                origem = a.nome if a else "Conta"
            elif pay.cartao_id is not None:
                c = cards_service.get(pay.cartao_id)
                origem = f"Cartão · {c.nome}" if c else "Cartão"
            PaymentRecordedDialog(self, pay.descricao, pay.valor, origem).exec()
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
            pay = dlg.payload()
            payments_service.update(pay)
            origem = "—"
            if pay.conta_id is not None:
                a = accounts_service.get(pay.conta_id)
                origem = a.nome if a else "Conta"
            elif pay.cartao_id is not None:
                c = cards_service.get(pay.cartao_id)
                origem = f"Cartão · {c.nome}" if c else "Cartão"
            PaymentRecordedDialog(self, pay.descricao, pay.valor, origem).exec()
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
