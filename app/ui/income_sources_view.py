"""Cadastro de fontes de renda mensal."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
)

from app.models.income_source import IncomeSource
from app.services import income_sources_service
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency


class IncomeSourceDialog(FormDialog):
    def __init__(self, parent=None, src: Optional[IncomeSource] = None) -> None:
        super().__init__("Editar fonte de renda" if src else "Nova fonte de renda", parent)
        self._src = src

        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Ex.: Salário, freelance, aluguel recebido...")

        self.ed_valor = QDoubleSpinBox()
        self.ed_valor.setRange(0.0, 10_000_000.0)
        self.ed_valor.setDecimals(2)
        self.ed_valor.setPrefix("R$ ")
        self.ed_valor.setSingleStep(100.0)

        self.ed_dia = QSpinBox()
        self.ed_dia.setRange(1, 31)
        self.ed_dia.setValue(5)

        self.chk_ativo = QCheckBox("Ativa (entra na renda mensal do dashboard)")
        self.chk_ativo.setChecked(True)

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Valor mensal *", self.ed_valor)
        self.form.addRow("Dia de recebimento *", self.ed_dia)
        self.form.addRow("", self.chk_ativo)
        self.form.addRow("Observação", self.ed_obs)

        if src:
            self.ed_nome.setText(src.nome)
            self.ed_valor.setValue(src.valor_mensal)
            self.ed_dia.setValue(src.dia_recebimento)
            self.chk_ativo.setChecked(src.ativo)
            self.ed_obs.setPlainText(src.observacao or "")

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.ed_valor.value() <= 0:
            return False, "Valor mensal deve ser maior que zero"
        return True, None

    def payload(self) -> IncomeSource:
        return IncomeSource(
            id=self._src.id if self._src else None,
            nome=self.ed_nome.text().strip(),
            valor_mensal=float(self.ed_valor.value()),
            ativo=self.chk_ativo.isChecked(),
            dia_recebimento=int(self.ed_dia.value()),
            observacao=self.ed_obs.toPlainText().strip() or None,
        )


class IncomeSourcesView(CrudPage):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__(
            "Renda",
            "Cadastre uma ou mais fontes de renda mensal. A soma das ativas aparece no dashboard.",
            ["Nome", "Valor mensal", "Dia receb.", "Ativa", "Observação"],
        )
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)
        self.reload()

    def reload(self) -> None:
        rows = []
        for s in income_sources_service.list_all():
            obs = (s.observacao or "").replace("\n", " ")
            if len(obs) > 80:
                obs = obs[:77] + "..."
            rows.append((s.id or 0, [
                s.nome,
                format_currency(s.valor_mensal),
                f"Dia {s.dia_recebimento:02d}",
                "Sim" if s.ativo else "Não",
                obs or "—",
            ]))
        self.model.set_rows(rows)

    def _add(self) -> None:
        dlg = IncomeSourceDialog(self)
        if dlg.exec():
            income_sources_service.create(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _edit(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Editar", "Selecione uma fonte de renda.")
            return
        src = income_sources_service.get(sid)
        if src is None:
            return
        dlg = IncomeSourceDialog(self, src)
        if dlg.exec():
            income_sources_service.update(dlg.payload())
            self.reload()
            self.data_changed.emit()

    def _delete(self) -> None:
        sid = self.selected_id()
        if sid is None:
            QMessageBox.information(self, "Excluir", "Selecione uma fonte de renda.")
            return
        resp = QMessageBox.question(
            self, "Excluir", "Excluir esta fonte de renda?"
        )
        if resp == QMessageBox.Yes:
            income_sources_service.delete(sid)
            self.reload()
            self.data_changed.emit()
