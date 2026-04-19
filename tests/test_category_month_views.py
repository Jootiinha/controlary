"""Agregação por categoria alinhada ao dashboard."""
from __future__ import annotations

from pathlib import Path

from app.charts import category_month_views
from app.database.connection import transaction
from app.services import dashboard_service

REF_MONTH = "2026-04"


def _seed_sample_data() -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta A', 1000)"
        )
        conn.execute(
            """
            INSERT INTO payments (valor, descricao, data, conta_id, forma_pagamento)
            VALUES (50.0, 'Lançamento teste', ?, 1, 'Pix')
            """,
            (f"{REF_MONTH}-15",),
        )


def test_fetch_cost_of_living_by_category_matches_cost_of_living(
    test_db_path: Path,
) -> None:
    _seed_sample_data()
    total = dashboard_service.cost_of_living(REF_MONTH)
    pairs = category_month_views.fetch_cost_of_living_by_category(REF_MONTH)
    s = sum(v for _, v in pairs)
    assert abs(s - total) < 0.02
