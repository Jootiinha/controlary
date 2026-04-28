"""Metas de investimento associadas a categorias."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.database.connection import use
from app.events import app_events
from app.models.investment_goal import InvestmentGoal
from app.repositories import investment_goals_repo, investments_repo


def list_all(
    include_inactive: bool = False, conn: Optional[sqlite3.Connection] = None
) -> List[InvestmentGoal]:
    with use(conn) as c:
        rows = investment_goals_repo.list_all(c, include_inactive)
    return [InvestmentGoal.from_row(r) for r in rows]


def get(
    goal_id: int, conn: Optional[sqlite3.Connection] = None
) -> Optional[InvestmentGoal]:
    with use(conn) as c:
        row = investment_goals_repo.get_row(c, goal_id)
    return InvestmentGoal.from_row(row) if row else None


def progress_aplicado(
    goal: InvestmentGoal, conn: Optional[sqlite3.Connection] = None
) -> float:
    if goal.category_id is None:
        return 0.0
    with use(conn) as c:
        return investments_repo.sum_aplicado_por_categoria(c, goal.category_id)


def progress_percent(aplicado: float, valor_alvo: float) -> float:
    if valor_alvo <= 0:
        return 0.0
    return (aplicado / valor_alvo) * 100.0


def create(goal: InvestmentGoal, conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        gid = investment_goals_repo.insert_goal(
            c,
            nome=goal.nome.strip(),
            valor_alvo=float(goal.valor_alvo),
            category_id=goal.category_id,
            data_alvo=goal.data_alvo,
            observacao=goal.observacao,
            ativo=1 if goal.ativo else 0,
        )
    app_events().investment_goals_changed.emit()
    return gid


def update(goal: InvestmentGoal, conn: Optional[sqlite3.Connection] = None) -> None:
    if goal.id is None:
        raise ValueError("Meta sem id")
    with use(conn) as c:
        investment_goals_repo.update_goal(
            c,
            goal_id=goal.id,
            nome=goal.nome.strip(),
            valor_alvo=float(goal.valor_alvo),
            category_id=goal.category_id,
            data_alvo=goal.data_alvo,
            observacao=goal.observacao,
            ativo=1 if goal.ativo else 0,
        )
    app_events().investment_goals_changed.emit()


def delete(goal_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        investment_goals_repo.delete_goal(c, goal_id)
    app_events().investment_goals_changed.emit()
