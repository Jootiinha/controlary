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
    QDoubleSpinBox,
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

        self.cmb_mirror = QComboBox()
        self.cmb_pagamento = QComboBox()
        for combo in (self.cmb_mirror, self.cmb_pagamento):
            combo.addItem("(Nenhuma)", None)
            for a in accounts_service.list_all():
                combo.addItem(a.nome, a.id)

        if fe.conta_id is not None:
            for i in range(self.cmb_mirror.count()):
                if self.cmb_mirror.itemData(i) == fe.conta_id:
                    self.cmb_mirror.setCurrentIndex(i)
                    break

        self.sp_valor = QDoubleSpinBox()
        self.sp_valor.setRange(0.0, 500_000.0)
        self.sp_valor.setDecimals(2)
        self.sp_valor.setPrefix("R$ ")
        self.sp_valor.setSingleStep(50.0)
        self.sp_valor.setValue(float(fe.valor_mensal))
        form = QFormLayout()
        form.addRow("", self.chk_mirror)
        form.addRow("Valor real pago *", self.sp_valor)
        form.addRow("Data do pagamento", self.dt)
        if fe.conta_id is not None:
            form.addRow("Conta do lançamento espelho", self.cmb_mirror)
        else:
            form.addRow("Conta utilizada no pagamento", self.cmb_pagamento)
        txt = QLabel(
            f"Confirma pagamento de {fe.nome} (estimativa cadastrada: "
            f"{format_currency(fe.valor_mensal)}) na competência {ano_mes}?"
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

    def valor_efetivo(self) -> float:
        return float(self.sp_valor.value())

    def conta_debito_para_livro(self) -> Optional[int]:
        """Conta para débito no livro-caixa quando o cadastro não tem conta; senão None."""
        if self._fe.conta_id is not None:
            return None
        cid = self.cmb_pagamento.currentData()
        return int(cid) if cid is not None else None

    def mirror_payment(self) -> Optional[Payment]:
        if not self.chk_mirror.isChecked():
            return None
        if self._fe.conta_id is not None:
            cid = self.cmb_mirror.currentData()
        else:
            cid = self.cmb_pagamento.currentData()
        if cid is None:
            return None
        return Payment(
            id=None,
            valor=self.valor_efetivo(),
            descricao=f"Fixo: {self._fe.nome} ({self._ano_mes})",
            data=self.dt.date().toString("yyyy-MM-dd"),
            conta_id=int(cid),
            cartao_id=None,
            forma_pagamento=self._fe.forma_pagamento,
            observacao=None,
            category_id=self._fe.category_id,
        )
