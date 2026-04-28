"""Testes de metas de investimento."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.category import Category
from app.models.investment import Investment
from app.models.investment_goal import InvestmentGoal
from app.services import categories_service, investment_goals_service, investments_service


def _bank() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Corretora', 0)"
        )
        return int(cur.lastrowid)


def test_goal_progress_sums_aplicado_por_categoria(test_db_path: Path) -> None:
    bid = _bank()
    cid = categories_service.create(
        Category(id=None, nome="Reserva", tipo_sugerido=None, cor=None, ativo=True)
    )
    investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="CDB A",
            tipo="CDB",
            valor_aplicado=3000.0,
            data_aplicacao="2026-01-01",
            category_id=cid,
        )
    )
    investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="CDB B",
            tipo="CDB",
            valor_aplicado=2000.0,
            data_aplicacao="2026-01-02",
            category_id=cid,
        )
    )
    gid = investment_goals_service.create(
        InvestmentGoal(
            id=None,
            nome="Meta reserva",
            valor_alvo=10_000.0,
            category_id=cid,
        )
    )
    g = investment_goals_service.get(gid)
    assert g is not None
    aplicado = investment_goals_service.progress_aplicado(g)
    assert aplicado == 5000.0
    pct = investment_goals_service.progress_percent(aplicado, g.valor_alvo)
    assert pct == pytest.approx(50.0)


def test_goal_sem_categoria_progresso_zero(test_db_path: Path) -> None:
    gid = investment_goals_service.create(
        InvestmentGoal(
            id=None,
            nome="Sem cat",
            valor_alvo=1000.0,
            category_id=None,
        )
    )
    g = investment_goals_service.get(gid)
    assert g is not None
    assert investment_goals_service.progress_aplicado(g) == 0.0
