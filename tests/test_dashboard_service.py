"""Testes de agregação do dashboard (sem UI)."""
from __future__ import annotations

from pathlib import Path

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
        conn.execute(
            """
            INSERT INTO income_sources (nome, valor_mensal, ativo, dia_recebimento)
            VALUES ('Salário', 5000.0, 1, 5)
            """
        )


def test_load_dashboard_totals_and_breakdown(test_db_path: Path) -> None:
    _seed_sample_data()
    data = dashboard_service.load(mes=REF_MONTH)

    assert data.mes_referencia == REF_MONTH
    assert data.total_gasto_mes == 50.0
    assert data.renda_mensal_total == 5000.0
    assert data.margem_apos_gasto == 4950.0
    assert data.gastos_por_conta == [("Conta A", 50.0)]
    assert data.gastos_por_forma == [("Pix", 50.0)]


def test_load_empty_database(test_db_path: Path) -> None:
    data = dashboard_service.load(mes=REF_MONTH)

    assert data.mes_referencia == REF_MONTH
    assert data.total_gasto_mes == 0.0
    assert data.renda_mensal_total == 0.0
    assert data.gastos_por_conta == []
    assert data.gastos_por_forma == []
