"""Cadastro de contas bancárias e cartões (listas usadas nos demais formulários)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.account import Account
from app.models.card import Card
from app.services import accounts_service, cards_service
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog


class AccountDialog(FormDialog):
    def __init__(self, parent=None, acc: Optional[Account] = None) -> None:
        super().__init__("Editar conta" if acc else "Nova conta bancária", parent)
        self._acc = acc

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Nubank, Conta corrente Itaú")

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Observação", self.ed_obs)

        if acc:
            self.ed_nome.setText(acc.nome)
            self.ed_obs.setPlainText(acc.observacao or "")

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Informe o nome da conta"
        return True, None

    def payload(self) -> Account:
        return Account(
            id=self._acc.id if self._acc else None,
            nome=self.ed_nome.text().strip(),
            observacao=self.ed_obs.toPlainText().strip() or None,
        )


class CardDialog(FormDialog):
    def __init__(self, parent=None, card: Optional[Card] = None) -> None:
        super().__init__("Editar cartão" if card else "Novo cartão", parent)
        self._card = card

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Visa Gold, Mastercard Nubank")

        self.cmb_conta = QComboBox()
        self.cmb_conta.setEditable(False)
        self._fill_contas()

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Conta vinculada", self.cmb_conta)
        self.form.addRow("Observação", self.ed_obs)

        if card:
            self.ed_nome.setText(card.nome)
            self.ed_obs.setPlainText(card.observacao or "")
            if card.account_id is not None:
                for i in range(self.cmb_conta.count()):
                    if self.cmb_conta.itemData(i) == card.account_id:
                        self.cmb_conta.setCurrentIndex(i)
                        break

    def _fill_contas(self) -> None:
        self.cmb_conta.clear()
        self.cmb_conta.addItem("(Nenhuma)", None)
        for a in accounts_service.list_all():
            self.cmb_conta.addItem(a.nome, a.id)

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Informe o nome do cartão"
        return True, None

    def payload(self) -> Card:
        aid = self.cmb_conta.currentData()
        return Card(
            id=self._card.id if self._card else None,
            nome=self.ed_nome.text().strip(),
            account_id=aid if aid is not None else None,
            observacao=self.ed_obs.toPlainText().strip() or None,
        )


class _AccountsCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Contas bancárias",
            "Cadastre contas para usar nos pagamentos e assinaturas.",
            ["Nome", "Observação"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)

    def reload(self) -> None:
        rows = []
        for a in accounts_service.list_all():
            rows.append((a.id or 0, [a.nome, a.observacao or ""]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        dlg = AccountDialog(self)
        if dlg.exec():
            accounts_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        aid = self.selected_id()
        if aid is None:
            QMessageBox.information(self, "Editar", "Selecione uma conta.")
            return
        acc = accounts_service.get(aid)
        if acc is None:
            return
        dlg = AccountDialog(self, acc)
        if dlg.exec():
            accounts_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        aid = self.selected_id()
        if aid is None:
            QMessageBox.information(self, "Excluir", "Selecione uma conta.")
            return
        if QMessageBox.question(self, "Excluir", "Excluir esta conta?") != QMessageBox.Yes:
            return
        try:
            accounts_service.delete(aid)
        except ValueError as e:
            QMessageBox.warning(self, "Não foi possível excluir", str(e))
            return
        self.reload()
        self.data_changed.emit()


class _CardsCrud(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Cartões",
            "Cadastre cartões para parcelamentos e assinaturas no crédito.",
            ["Nome", "Conta vinculada", "Observação"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)

    def reload(self) -> None:
        rows = []
        for c in cards_service.list_all():
            vinc = c.conta_nome or "—"
            rows.append((c.id or 0, [c.nome, vinc, c.observacao or ""]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        dlg = CardDialog(self)
        if dlg.exec():
            cards_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        cid = self.selected_id()
        if cid is None:
            QMessageBox.information(self, "Editar", "Selecione um cartão.")
            return
        card = cards_service.get(cid)
        if card is None:
            return
        dlg = CardDialog(self, card)
        if dlg.exec():
            cards_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        cid = self.selected_id()
        if cid is None:
            QMessageBox.information(self, "Excluir", "Selecione um cartão.")
            return
        if QMessageBox.question(self, "Excluir", "Excluir este cartão?") != QMessageBox.Yes:
            return
        try:
            cards_service.delete(cid)
        except ValueError as e:
            QMessageBox.warning(self, "Não foi possível excluir", str(e))
            return
        self.reload()
        self.data_changed.emit()


class AccountsCardsView(QWidget):
    """Aba com cadastro de contas e de cartões."""

    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._acc = _AccountsCrud()
        self._card = _CardsCrud()
        self._acc.data_changed.connect(self.data_changed.emit)
        self._card.data_changed.connect(self.data_changed.emit)

        tabs = QTabWidget()
        tabs.addTab(self._acc, "Contas")
        tabs.addTab(self._card, "Cartões")

        hint = QLabel(
            "Cadastre ao menos uma conta e, se usar crédito, um cartão. "
            "Esses itens aparecem nas listas de Pagamentos, Parcelamentos e Assinaturas."
        )
        hint.setWordWrap(True)
        hint.setObjectName("PageSubtitle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(hint)
        layout.addWidget(tabs, 1)

    def reload(self) -> None:
        self._acc.reload()
        self._card.reload()
