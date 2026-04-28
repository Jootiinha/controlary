"""CRUD de metas de investimento por categoria."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDoubleSpinBox,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
)

from app.events import app_events
from app.models.investment_goal import InvestmentGoal
from app.services import categories_service, investment_goals_service
from app.ui.categories_view import CategoryDialog
from app.ui.widgets.category_picker import CategoryPicker, emit_parent_view_data_changed
from app.ui.widgets.crud_page import CrudPage
from app.ui.widgets.form_dialog import FormDialog
from app.utils.formatting import format_currency, format_date_br


def _fmt_pct(pct: float) -> str:
    s = f"{pct:.1f}".replace(".", ",")
    return f"{s} %"


class GoalDialog(FormDialog):
    def __init__(self, parent=None, goal: Optional[InvestmentGoal] = None) -> None:
        super().__init__("Editar meta" if goal else "Nova meta", parent)
        self._goal = goal

        self.ed_nome = QLineEdit()

        self.sp_alvo = QDoubleSpinBox()
        self.sp_alvo.setRange(0.01, 99_999_999.0)
        self.sp_alvo.setDecimals(2)
        self.sp_alvo.setPrefix("R$ ")

        self._picker_cat = CategoryPicker(self, allow_empty=True)
        self._picker_cat.connect_new_button(self._nova_cat)

        self.dt_alvo = QDateEdit()
        self.dt_alvo.setDisplayFormat("dd/MM/yyyy")
        self.dt_alvo.setCalendarPopup(True)
        self.dt_alvo.setSpecialValueText("—")
        self.dt_alvo.setMinimumDate(QDate(1900, 1, 1))

        self.ed_obs = QPlainTextEdit()
        self.ed_obs.setFixedHeight(64)

        self.form.addRow("Nome *", self.ed_nome)
        self.form.addRow("Valor alvo *", self.sp_alvo)
        self.form.addRow("Categoria", self._picker_cat)
        self.form.addRow("Data alvo", self.dt_alvo)
        self.form.addRow("Observação", self.ed_obs)

        if goal:
            self.ed_nome.setText(goal.nome)
            self.sp_alvo.setValue(goal.valor_alvo)
            if goal.category_id is not None:
                self._picker_cat.set_category_id(goal.category_id)
            if goal.data_alvo:
                self.dt_alvo.setDate(QDate.fromString(goal.data_alvo, "yyyy-MM-dd"))
            else:
                self.dt_alvo.setDate(QDate(1900, 1, 1))
            self.ed_obs.setPlainText(goal.observacao or "")
        else:
            self.dt_alvo.setDate(QDate(1900, 1, 1))

    def _nova_cat(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            categories_service.create(dlg.payload())
            self._picker_cat.reload_from_db()
            emit_parent_view_data_changed(self)

    def validate(self) -> tuple[bool, str | None]:
        if not self.ed_nome.text().strip():
            return False, "Nome é obrigatório"
        if self.sp_alvo.value() <= 0:
            return False, "Valor alvo deve ser maior que zero"
        return True, None

    def payload(self) -> InvestmentGoal:
        dt = self.dt_alvo.date()
        data_alvo = None if dt == QDate(1900, 1, 1) else dt.toString("yyyy-MM-dd")
        return InvestmentGoal(
            id=self._goal.id if self._goal else None,
            nome=self.ed_nome.text().strip(),
            valor_alvo=float(self.sp_alvo.value()),
            category_id=self._picker_cat.current_category_id(),
            data_alvo=data_alvo,
            observacao=self.ed_obs.toPlainText().strip() or None,
            ativo=True if self._goal is None else self._goal.ativo,
        )


class InvestmentGoalsView(CrudPage):
    def __init__(self) -> None:
        super().__init__(
            "Metas de investimento",
            "Defina valores alvo por categoria. O progresso soma o valor aplicado dos "
            "investimentos ativos na mesma categoria.",
            ["Nome", "Categoria", "Alvo", "Progresso", "%", "Data-alvo"],
        )
        self._progress_by_id: dict[int, float] = {}
        self._goals_by_id: dict[int, InvestmentGoal] = {}

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self.reload)

        ev = app_events()
        ev.investments_changed.connect(self.reload)
        ev.categories_changed.connect(self.reload)

        self.reload()

    def reload(self) -> None:
        rows: list[tuple[int, list[str]]] = []
        self._progress_by_id.clear()
        self._goals_by_id.clear()
        for g in investment_goals_service.list_all(include_inactive=False):
            if g.id is None:
                continue
            aplicado = investment_goals_service.progress_aplicado(g)
            pct = investment_goals_service.progress_percent(aplicado, g.valor_alvo)
            self._progress_by_id[g.id] = aplicado
            self._goals_by_id[g.id] = g
            rows.append(
                (
                    g.id,
                    [
                        g.nome,
                        g.categoria_nome or "—",
                        format_currency(g.valor_alvo),
                        format_currency(aplicado),
                        _fmt_pct(pct),
                        format_date_br(g.data_alvo) if g.data_alvo else "—",
                    ],
                )
            )
        self.model.set_rows(rows)
        self.refresh_totals()

    def compute_totals(self, visible_ids: list[int]) -> None:
        sum_alvo = 0.0
        sum_prog = 0.0
        for gid in visible_ids:
            g = self._goals_by_id.get(gid)
            if g is None:
                continue
            sum_alvo += float(g.valor_alvo)
            sum_prog += self._progress_by_id.get(gid, 0.0)
        self.set_footer_text(
            f"Total alvo (filtrado): {format_currency(sum_alvo)}",
            f"Progresso (filtrado): {format_currency(sum_prog)}",
        )

    def _add(self) -> None:
        dlg = GoalDialog(self)
        if dlg.exec():
            investment_goals_service.create(dlg.payload())
            self.reload()

    def _edit(self) -> None:
        gid = self.selected_id()
        if gid is None:
            QMessageBox.information(self, "Editar", "Selecione uma meta.")
            return
        goal = investment_goals_service.get(gid)
        if goal is None:
            return
        dlg = GoalDialog(self, goal)
        if dlg.exec():
            investment_goals_service.update(dlg.payload())
            self.reload()

    def _delete(self) -> None:
        gid = self.selected_id()
        if gid is None:
            QMessageBox.information(self, "Excluir", "Selecione uma meta.")
            return
        if (
            QMessageBox.question(
                self,
                "Excluir",
                "Excluir esta meta permanentemente?",
            )
            != QMessageBox.Yes
        ):
            return
        investment_goals_service.delete(gid)
        self.reload()
