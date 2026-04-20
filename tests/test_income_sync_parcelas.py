"""Reduzir parcelas_recebidas remove crédito de renda no livro-caixa."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.models.income_source import IncomeSource
from app.services import accounts_service, income_sources_service


def test_reduce_parcelas_recebidas_removes_ledger(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('C1', 0)")
    src = IncomeSource(
        id=None,
        nome="Venda parcelada",
        valor_mensal=50.0,
        ativo=True,
        dia_recebimento=5,
        account_id=1,
        tipo="parcelada",
        mes_referencia="2026-01",
        total_parcelas=3,
        parcelas_recebidas=2,
    )
    sid = income_sources_service.create(src)
    key1 = accounts_service.transaction_key_income(sid, "2026-01")
    key2 = accounts_service.transaction_key_income(sid, "2026-02")
    with transaction() as conn:
        assert conn.execute(
            "SELECT COUNT(*) AS n FROM account_transactions WHERE transaction_key IN (?, ?)",
            (key1, key2),
        ).fetchone()["n"] == 2

    income_sources_service.update(
        IncomeSource(
            id=sid,
            nome="Venda parcelada",
            valor_mensal=50.0,
            ativo=True,
            dia_recebimento=5,
            account_id=1,
            tipo="parcelada",
            mes_referencia="2026-01",
            total_parcelas=3,
            parcelas_recebidas=0,
        )
    )
    with transaction() as conn:
        assert conn.execute(
            "SELECT COUNT(*) AS n FROM account_transactions WHERE transaction_key LIKE ?",
            (f"income:{sid}:%",),
        ).fetchone()["n"] == 0
