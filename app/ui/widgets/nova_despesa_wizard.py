from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services import (
    accounts_service,
    cards_service,
    fixed_expenses_service,
    installments_service,
    payments_service,
    subscriptions_service,
)
from app.ui.fixed_expenses_view import FixedExpenseDialog
from app.ui.installments_view import InstallmentDialog
from app.ui.payments_view import PaymentDialog
from app.ui.subscriptions_view import SubscriptionDialog


class NovaDespesaTypeDialog(QDialog):
    """Passo 1: escolher o tipo de despesa."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova despesa")
        self.setModal(True)
        self._chosen: str | None = None
        sub = QLabel("O que você quer registrar?")
        sub.setObjectName("PageSubtitle")
        grid = QGridLayout()
        grid.setSpacing(12)
        opts: list[tuple[str, str, str]] = [
            (
                "avulsa",
                "Despesa avulsa",
                "Compra pontual em conta ou no cartão (supermercado, farmácia…).",
            ),
            (
                "parcelada",
                "Despesa parcelada",
                "Compra dividida em várias parcelas (cartão ou conta).",
            ),
            (
                "assinatura",
                "Assinatura",
                "Cobrança recorrente (streaming, software, academia…).",
            ),
            (
                "fixa",
                "Despesa fixa",
                "Conta que se repete todo mês (aluguel, condomínio, escola…).",
            ),
        ]
        for i, (key, title, hint) in enumerate(opts):
            btn = QPushButton(f"{title}\n{hint}")
            btn.setMinimumHeight(72)
            btn.setStyleSheet("text-align: left; padding: 12px;")
            btn.clicked.connect(lambda checked=False, k=key: self._pick(k))
            grid.addWidget(btn, i // 2, i % 2)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        bb.rejected.connect(self.reject)
        outer = QVBoxLayout(self)
        outer.addWidget(sub)
        outer.addLayout(grid)
        outer.addWidget(bb)

    def _pick(self, key: str) -> None:
        self._chosen = key
        self.accept()

    def chosen(self) -> str | None:
        return self._chosen


def open_nova_despesa_flow(
    parent: QWidget,
    *,
    show_toast: Callable[[str], None],
) -> None:
    """Abre escolha do tipo e o formulário correspondente; emite toast ao salvar."""
    if not accounts_service.list_all() and not cards_service.list_all():
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            parent,
            "Cadastre uma origem",
            "Cadastre ao menos uma conta ou cartão em Contas ou Cartões.",
        )
        return
    step = NovaDespesaTypeDialog(parent)
    if step.exec() != QDialog.DialogCode.Accepted:
        return
    typ = step.chosen()
    if typ == "avulsa":
        dlg = PaymentDialog(parent)
        if dlg.exec():
            pay = dlg.payload()
            payments_service.create(pay)
            show_toast(f"Despesa avulsa registrada: {pay.descricao}.")
        return
    if typ == "parcelada":
        dlg = InstallmentDialog(parent)
        if dlg.exec():
            inst = dlg.payload()
            installments_service.create(inst)
            show_toast(f"Despesa parcelada registrada: {inst.nome_fatura}.")
        return
    if typ == "assinatura":
        dlg = SubscriptionDialog(parent)
        if dlg.exec():
            subscription = dlg.payload()
            subscriptions_service.create(subscription)
            show_toast(f"Assinatura registrada: {subscription.nome}.")
        return
    if typ == "fixa":
        dlg = FixedExpenseDialog(parent)
        if dlg.exec():
            fe = dlg.payload()
            fixed_expenses_service.create(fe)
            show_toast(f"Despesa fixa registrada: {fe.nome}.")
        return
