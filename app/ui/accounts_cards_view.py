"""Cadastro de contas bancárias e cartões (listas usadas nos demais formulários)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from app.models.account import Account
from app.models.card import Card
from app.services import accounts_service, cards_service
from app.ui.widgets.card import KpiCard
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency


class BalanceAdjustDialog(QDialog):
    """Ajuste manual no livro-caixa (delta em R$ e data)."""

    def __init__(self, parent=None, nome_conta: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajustar saldo")
        self.ed_delta = QDoubleSpinBox()
        self.ed_delta.setRange(-10_000_000.0, 10_000_000.0)
        self.ed_delta.setDecimals(2)
        self.ed_delta.setPrefix("R$ ")
        self.ed_data = QDateEdit()
        self.ed_data.setDisplayFormat("dd/MM/yyyy")
        self.ed_data.setCalendarPopup(True)
        self.ed_data.setDate(QDate.currentDate())
        form = QFormLayout()
        if nome_conta:
            form.addRow("Conta", QLabel(nome_conta))
        form.addRow("Valor do ajuste (+ ou −) *", self.ed_delta)
        form.addRow("Data *", self.ed_data)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(btns)

    def data_iso(self) -> str:
        return self.ed_data.date().toString("yyyy-MM-dd")

    def delta(self) -> float:
        return float(self.ed_delta.value())


class TransferBetweenAccountsDialog(QDialog):
    """Débito na origem e crédito no destino no livro-caixa (não é despesa)."""

    def __init__(self, parent=None, preferred_from_id: Optional[int] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Transferir entre contas")
        hint = QLabel(
            "Registra saída na conta de origem e entrada na de destino. "
            "Não entra como despesa nos totais do mês."
        )
        hint.setWordWrap(True)
        hint.setObjectName("FormHint")
        self.cmb_from = QComboBox()
        self.cmb_to = QComboBox()
        self._fill_combo(self.cmb_from)
        self._fill_combo(self.cmb_to)
        if preferred_from_id is not None:
            for i in range(self.cmb_from.count()):
                if self.cmb_from.itemData(i) == preferred_from_id:
                    self.cmb_from.setCurrentIndex(i)
                    break
        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.01, 10_000_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(10.0)
        self.ed_data = QDateEdit()
        self.ed_data.setDisplayFormat("dd/MM/yyyy")
        self.ed_data.setCalendarPopup(True)
        self.ed_data.setDate(QDate.currentDate())
        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(56)
        self.ed_obs.setPlaceholderText("Opcional")
        form = QFormLayout()
        form.addRow("", hint)
        form.addRow("Conta de origem *", self.cmb_from)
        form.addRow("Conta de destino *", self.cmb_to)
        form.addRow("Valor *", self.ed_valor)
        form.addRow("Data *", self.ed_data)
        form.addRow("Observação", self.ed_obs)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(btns)

    def _fill_combo(self, combo: QComboBox) -> None:
        combo.clear()
        for a in accounts_service.list_all():
            if a.id is not None:
                combo.addItem(a.nome, int(a.id))

    def from_account_id(self) -> Optional[int]:
        d = self.cmb_from.currentData()
        return int(d) if d is not None else None

    def to_account_id(self) -> Optional[int]:
        d = self.cmb_to.currentData()
        return int(d) if d is not None else None

    def valor(self) -> float:
        return float(self.ed_valor.value())

    def data_iso(self) -> str:
        return self.ed_data.date().toString("yyyy-MM-dd")

    def observacao(self) -> Optional[str]:
        t = self.ed_obs.toPlainText().strip()
        return t or None


class AccountDialog(FormDialog):
    def __init__(self, parent=None, acc: Optional[Account] = None) -> None:
        super().__init__("Editar conta" if acc else "Nova conta bancária", parent)
        self._acc = acc

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Nubank, Conta corrente Itaú")

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.ed_saldo_ini = QDoubleSpinBox()
        self.ed_saldo_ini.setRange(-10_000_000.0, 10_000_000.0)
        self.ed_saldo_ini.setDecimals(2)
        self.ed_saldo_ini.setPrefix("R$ ")

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Saldo inicial", self.ed_saldo_ini)
        self.form.addRow("Observação", self.ed_obs)

        if acc:
            self.ed_nome.setText(acc.nome)
            self.ed_obs.setPlainText(acc.observacao or "")
            self.ed_saldo_ini.setValue(float(acc.saldo_inicial))

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Informe o nome da conta"
        return True, None

    def payload(self) -> Account:
        return Account(
            id=self._acc.id if self._acc else None,
            nome=self.ed_nome.text().strip(),
            observacao=self.ed_obs.toPlainText().strip() or None,
            saldo_inicial=float(self.ed_saldo_ini.value()),
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

        self.ed_dia_fatura = QSpinBox()
        self.ed_dia_fatura.setRange(1, 31)
        self.ed_dia_fatura.setValue(10)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Conta vinculada", self.cmb_conta)
        self.form.addRow("Dia de pagamento da fatura *", self.ed_dia_fatura)
        self.form.addRow("Observação", self.ed_obs)

        if card:
            self.ed_nome.setText(card.nome)
            self.ed_dia_fatura.setValue(card.dia_pagamento_fatura)
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
            dia_pagamento_fatura=int(self.ed_dia_fatura.value()),
        )


class AccountsCrudView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Contas bancárias",
            "Cadastre contas para usar nos pagamentos e assinaturas. "
            "Saldo atual = saldo inicial + movimentações até hoje.",
            ["Nome", "Saldo inicial", "Saldo atual", "Observação"],
        )
        self.btn_adjust = QPushButton("Ajustar saldo…")
        self.btn_adjust.setToolTip(
            "Registra um ajuste manual no livro-caixa (ex.: conciliação com extrato)."
        )
        self.btn_adjust.clicked.connect(self._adjust_balance)
        self.btn_transfer = QPushButton("Transferir entre contas…")
        self.btn_transfer.setToolTip(
            "Move valor da conta de origem para a de destino no livro-caixa. "
            "Não conta como despesa nos totais mensais."
        )
        self.btn_transfer.clicked.connect(self._transfer_between_accounts)
        adj_row = QWidget()
        adj_lay = QHBoxLayout(adj_row)
        adj_lay.setContentsMargins(0, 0, 0, 0)
        adj_lay.addWidget(self.btn_adjust)
        adj_lay.addWidget(self.btn_transfer)
        adj_lay.addStretch()
        self._main_layout.insertWidget(2, adj_row)

        self.totals_wrap.setVisible(True)
        self._kp_saldo = KpiCard(
            "Saldo total",
            "-",
            "Soma dos saldos atuais",
            compact=True,
        )
        self._kp_ncontas = KpiCard(
            "Contas cadastradas",
            "-",
            "No cadastro",
            compact=True,
        )
        self._kp_ncartoes = KpiCard(
            "Cartões cadastrados",
            "-",
            "No cadastro",
            compact=True,
        )
        self.totals_bar.addWidget(self._kp_saldo)
        self.totals_bar.addWidget(self._kp_ncontas)
        self.totals_bar.addWidget(self._kp_ncartoes)

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)

    def _refresh_kpi_cards(self) -> None:
        contas = accounts_service.list_all()
        self._kp_saldo.set_value(format_currency(accounts_service.sum_balances()))
        self._kp_ncontas.set_value(str(len(contas)))
        self._kp_ncartoes.set_value(str(len(cards_service.list_all())))

    def reload(self) -> None:
        rows = []
        for a in accounts_service.list_all():
            sa = a.saldo_atual
            rows.append((
                a.id or 0,
                [
                    a.nome,
                    format_currency(float(a.saldo_inicial)),
                    format_currency(float(sa)) if sa is not None else "—",
                    a.observacao or "",
                ],
            ))
        self.model.set_rows(rows)
        self._refresh_kpi_cards()

    def _adjust_balance(self) -> None:
        aid = self.selected_id()
        if aid is None:
            QMessageBox.information(self, "Ajustar saldo", "Selecione uma conta.")
            return
        acc = accounts_service.get(aid)
        if acc is None:
            return
        dlg = BalanceAdjustDialog(self, nome_conta=acc.nome)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.delta()
        if abs(d) < 0.005:
            QMessageBox.information(self, "Ajustar saldo", "Informe um valor diferente de zero.")
            return
        accounts_service.post_adjustment(
            aid,
            d,
            dlg.data_iso(),
            descricao="Ajuste manual",
        )
        self.reload()
        self.data_changed.emit()

    def _transfer_between_accounts(self) -> None:
        contas = accounts_service.list_all()
        if len(contas) < 2:
            QMessageBox.information(
                self,
                "Transferir",
                "Cadastre ao menos duas contas para transferir entre elas.",
            )
            return
        aid = self.selected_id()
        dlg = TransferBetweenAccountsDialog(self, preferred_from_id=aid)
        if dlg.exec() != QDialog.Accepted:
            return
        fid = dlg.from_account_id()
        tid = dlg.to_account_id()
        if fid is None or tid is None:
            QMessageBox.warning(self, "Transferir", "Selecione origem e destino.")
            return
        if fid == tid:
            QMessageBox.warning(
                self, "Transferir", "A conta de origem deve ser diferente da de destino."
            )
            return
        v = dlg.valor()
        if v <= 0:
            QMessageBox.warning(self, "Transferir", "Informe um valor maior que zero.")
            return
        try:
            accounts_service.post_transfer(
                fid,
                tid,
                v,
                dlg.data_iso(),
                descricao=dlg.observacao(),
            )
        except ValueError as e:
            QMessageBox.warning(self, "Transferir", str(e))
            return
        self.reload()
        self.data_changed.emit()

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
        if (
            QMessageBox.question(
                self,
                "Excluir",
                "Excluir esta conta remove também o histórico de movimentações "
                "(livro-caixa) e vínculos que dependam dela.",
            )
            != QMessageBox.Yes
        ):
            return
        try:
            accounts_service.delete(aid)
        except ValueError as e:
            QMessageBox.warning(self, "Não foi possível excluir", str(e))
            return
        self.reload()
        self.data_changed.emit()


class CardsCrudView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Cartões",
            "Cadastre cartões para parcelamentos e assinaturas no crédito.",
            ["Nome", "Conta vinculada", "Venc. fatura", "Observação"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)

    def reload(self) -> None:
        rows = []
        for c in cards_service.list_all():
            vinc = c.conta_nome or "—"
            rows.append((
                c.id or 0,
                [
                    c.nome,
                    vinc,
                    f"Dia {c.dia_pagamento_fatura:02d}",
                    c.observacao or "",
                ],
            ))
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
        if (
            QMessageBox.question(
                self,
                "Excluir",
                "Excluir este cartão remove faturas, parcelamentos e referências "
                "associadas a ele.",
            )
            != QMessageBox.Yes
        ):
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

    def __init__(self) -> None:
        super().__init__()
        self._acc = AccountsCrudView()
        self._card = CardsCrudView()
        self._acc.data_changed.connect(self._card.reload)
        self._card.data_changed.connect(self._acc.reload)

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
