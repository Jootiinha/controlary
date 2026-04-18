"""Confirmações após registrar pagamentos e ao marcar fixo como pago."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from app.models.fixed_expense import FixedExpense
from app.models.payment import Payment
from app.services import accounts_service
from app.utils.formatting import format_currency


class PaymentRecordedDialog(QDialog):
    """Resumo após criar/editar pagamento avulso."""

    def __init__(
        self,
        parent,
        descricao: str,
        valor: float,
        origem_label: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pagamento registrado")
        lbl = QLabel(
            f"{descricao}\n"
            f"{format_currency(valor)} · {origem_label}"
        )
        lbl.setWordWrap(True)
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        lay = QVBoxLayout(self)
        lay.addWidget(lbl)
        lay.addWidget(btns)


class FixedExpensePaidDialog(QDialog):
    """Ao marcar fixo como pago: opcionalmente cria espelho em Pagamentos."""

    def __init__(self, parent, fe: FixedExpense, ano_mes: str) -> None:
        super().__init__(parent)
        self._fe = fe
        self._ano_mes = ano_mes
        self.setWindowTitle("Confirmar pagamento")
        self.chk_mirror = QCheckBox(
            "Criar lançamento espelho em Pagamentos (mesmo valor e categoria)"
        )
        self.chk_mirror.setChecked(True)
        self.dt = QDateEdit()
        self.dt.setDisplayFormat("dd/MM/yyyy")
        self.dt.setCalendarPopup(True)
        self.dt.setDate(QDate.currentDate())
        self.cmb_conta = QComboBox()
        self.cmb_conta.addItem("(Nenhuma)", None)
        for a in accounts_service.list_all():
            self.cmb_conta.addItem(a.nome, a.id)
        if fe.conta_id is not None:
            for i in range(self.cmb_conta.count()):
                if self.cmb_conta.itemData(i) == fe.conta_id:
                    self.cmb_conta.setCurrentIndex(i)
                    break
        form = QFormLayout()
        form.addRow("", self.chk_mirror)
        form.addRow("Data do pagamento", self.dt)
        form.addRow("Conta do lançamento espelho", self.cmb_conta)
        txt = QLabel(
            f"Confirma pagamento de {fe.nome} ({format_currency(fe.valor_mensal)}) "
            f"na competência {ano_mes}?"
        )
        txt.setWordWrap(True)
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addWidget(txt)
        lay.addLayout(form)
        lay.addWidget(btns)

    def mirror_payment(self) -> Optional[Payment]:
        if not self.chk_mirror.isChecked():
            return None
        cid = self.cmb_conta.currentData()
        if cid is None:
            return None
        return Payment(
            id=None,
            valor=float(self._fe.valor_mensal),
            descricao=f"Fixo: {self._fe.nome} ({self._ano_mes})",
            data=self.dt.date().toString("yyyy-MM-dd"),
            conta_id=int(cid),
            cartao_id=None,
            forma_pagamento=self._fe.forma_pagamento,
            observacao=None,
            category_id=self._fe.category_id,
        )
