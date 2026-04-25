"""Agregação por categoria alinhada ao dashboard."""
from __future__ import annotations

from pathlib import Path

from app.charts import category_month_views
from app.database.connection import transaction
from app.services import accounts_service, dashboard_service

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


def test_fetch_ledger_by_category_ignora_ajuste(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta L', 1000)"
        )
        cur = conn.execute(
            """
            INSERT INTO payments (valor, descricao, data, conta_id, forma_pagamento)
            VALUES (25.0, 'Item', ?, 1, 'Pix')
            """,
            (f"{REF_MONTH}-05",),
        )
        pid = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (1, ?, -25.0, 'pagamento', ?, 'Item')
            """,
            (
                f"{REF_MONTH}-05",
                accounts_service.transaction_key_payment(pid),
            ),
        )
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (1, ?, -999.0, 'ajuste', 'adjustment:abc', 'x')
            """,
            (f"{REF_MONTH}-06",),
        )
    pairs = category_month_views.fetch_ledger_by_category(REF_MONTH)
    labels = [k for k, _ in pairs]
    assert "Ajuste" not in labels
    assert sum(v for _, v in pairs) == 25.0
