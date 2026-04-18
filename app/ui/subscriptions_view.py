"""Tela de CRUD de assinaturas recorrentes."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
)

from app.models.subscription import Subscription
from app.services import accounts_service, cards_service, subscriptions_service
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency


STATUS_ASSINATURA = ["ativa", "pausada", "cancelada"]
FORMAS = ["Pix", "Débito", "Crédito", "Boleto", "Transferência"]
CATEGORIAS = [
    "Streaming", "Software", "Música", "Academia",
    "Jogos", "Educação", "Notícias", "Outros",
]


class SubscriptionDialog(FormDialog):
    def __init__(self, parent=None, sub: Optional[Subscription] = None) -> None:
        super().__init__("Editar assinatura" if sub else "Nova assinatura", parent)
        self._sub = sub

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Netflix, Spotify, ChatGPT...")

        self.ed_categoria = QComboBox()
        self.ed_categoria.setEditable(True)
        self.ed_categoria.addItems(CATEGORIAS)

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 100_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(5.0)

        self.ed_dia = QSpinBox()
        self.ed_dia.setRange(1, 31)
        self.ed_dia.setValue(1)

        self.ed_forma = QComboBox()
        self.ed_forma.addItems(FORMAS)

        self.cmb_meio = QComboBox()
        self.cmb_meio.setEditable(False)
        self._fill_meio()

        self.ed_status = QComboBox()
        self.ed_status.addItems(STATUS_ASSINATURA)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(70)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Categoria", self.ed_categoria)
        self.form.addRow("Valor mensal *", self.ed_valor)
        self.form.addRow("Dia da cobrança *", self.ed_dia)
        self.form.addRow("Forma de pagamento *", self.ed_forma)
        self.form.addRow("Conta ou cartão", self.cmb_meio)
        self.form.addRow("Status *", self.ed_status)
        self.form.addRow("Observação", self.ed_obs)

        if sub:
            self.ed_nome.setText(sub.nome)
            if sub.categoria:
                idx = self.ed_categoria.findText(sub.categoria)
                if idx >= 0:
                    self.ed_categoria.setCurrentIndex(idx)
                else:
                    self.ed_categoria.setEditText(sub.categoria)
            self.ed_valor.setValue(sub.valor_mensal)
            self.ed_dia.setValue(sub.dia_cobranca)
            idx = self.ed_forma.findText(sub.forma_pagamento)
            if idx >= 0:
                self.ed_forma.setCurrentIndex(idx)
            idx = self.ed_status.findText(sub.status)
            if idx >= 0:
                self.ed_status.setCurrentIndex(idx)
            self.ed_obs.setPlainText(sub.observacao or "")
            self._select_meio(sub)

    def _fill_meio(self) -> None:
        self.cmb_meio.clear()
        self.cmb_meio.addItem("(Nenhum)", None)
        for a in accounts_service.list_all():
            self.cmb_meio.addItem(f"Conta · {a.nome}", f"acc:{a.id}")
        for c in cards_service.list_all():
            self.cmb_meio.addItem(f"Cartão · {c.nome}", f"card:{c.id}")

    def _select_meio(self, sub: Subscription) -> None:
        for i in range(self.cmb_meio.count()):
            data = self.cmb_meio.itemData(i)
            if not data or not isinstance(data, str):
                continue
            kind, _, mid = data.partition(":")
            if not mid:
                continue
            try:
                iid = int(mid)
            except ValueError:
                continue
            if sub.account_id and kind == "acc" and iid == sub.account_id:
                self.cmb_meio.setCurrentIndex(i)
                return
            if sub.card_id and kind == "card" and iid == sub.card_id:
                self.cmb_meio.setCurrentIndex(i)
                return

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.ed_valor.value() <= 0:
            return False, "Valor mensal deve ser maior que zero"
        return True, None

    def payload(self) -> Subscription:
        account_id: Optional[int] = None
        card_id: Optional[int] = None
        raw = self.cmb_meio.currentData()
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
        return Subscription(
            id=self._sub.id if self._sub else None,
            nome=self.ed_nome.text().strip(),
            categoria=self.ed_categoria.currentText().strip() or None,
            valor_mensal=float(self.ed_valor.value()),
            dia_cobranca=int(self.ed_dia.value()),
            forma_pagamento=self.ed_forma.currentText(),
            status=self.ed_status.currentText(),
            observacao=self.ed_obs.toPlainText().strip() or None,
            account_id=account_id,
            card_id=card_id,
        )


class SubscriptionsView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Assinaturas",
            "Gerencie assinaturas recorrentes e o custo mensal total.",
            ["Nome", "Categoria", "Valor", "Dia", "Forma", "Conta/Cartão", "Status"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def reload(self) -> None:
        rows = []
        for s in subscriptions_service.list_all():
            meio = s.meio_label or "—"
            rows.append((s.id or 0, [
                s.nome,
                s.categoria or "",
                format_currency(s.valor_mensal),
                f"Dia {s.dia_cobranca:02d}",
                s.forma_pagamento,
                meio,
                s.status.capitalize(),
            ]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        dlg = SubscriptionDialog(self)
        if dlg.exec():
            subscriptions_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Editar", "Selecione uma assinatura.")
            return
        sub = subscriptions_service.get(sid)
        if sub is None:
            return
        dlg = SubscriptionDialog(self, sub)
        if dlg.exec():
            subscriptions_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Excluir", "Selecione uma assinatura.")
            return
        resp = QMessageBox.question(
            self, "Excluir", "Excluir esta assinatura?"
        )
        if resp == QMessageBox.Yes:
            subscriptions_service.delete(sid)
            self.reload()
            self.data_changed.emit()
