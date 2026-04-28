"""Transferências entre contas no livro-caixa."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.models.payment import Payment
from app.services import accounts_service, expense_totals_service, payments_service


def _two_accounts() -> tuple[int, int]:
    with transaction() as conn:
        c1 = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Origem', 1000.0)"
        ).lastrowid
        c2 = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Destino', 500.0)"
        ).lastrowid
    return int(c1), int(c2)


def test_post_transfer_two_ledger_rows_and_balances(test_db_path: Path) -> None:
    a1, a2 = _two_accounts()
    accounts_service.post_transfer(a1, a2, 200.0, "2026-04-15")
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT account_id, valor, origem, transaction_key
              FROM account_transactions
             WHERE transaction_key LIKE 'transfer:%'
             ORDER BY valor
            """
        ).fetchall()
    assert len(rows) == 2
    assert int(rows[0]["account_id"]) == a1
    assert float(rows[0]["valor"]) == -200.0
    assert rows[0]["origem"] == "transferencia"
    assert str(rows[0]["transaction_key"]).endswith(":debit")
    assert int(rows[1]["account_id"]) == a2
    assert float(rows[1]["valor"]) == 200.0
    assert rows[1]["origem"] == "transferencia"
    assert str(rows[1]["transaction_key"]).endswith(":credit")
    assert accounts_service.current_balance(a1) == 800.0
    assert accounts_service.current_balance(a2) == 700.0


def test_post_transfer_excluded_from_total_despesa_mes(test_db_path: Path) -> None:
    a1, a2 = _two_accounts()
    accounts_service.post_transfer(a1, a2, 300.0, "2026-05-10")
    payments_service.create(
        Payment(
            id=None,
            valor=50.0,
            descricao="Pix",
            data="2026-05-12",
            conta_id=a1,
            forma_pagamento="Pix",
        ),
        record_ledger=True,
    )
    assert expense_totals_service.total_despesa_mes("2026-05") == 50.0


def test_post_transfer_same_account_raises(test_db_path: Path) -> None:
    a1, _ = _two_accounts()
    try:
        accounts_service.post_transfer(a1, a1, 10.0, "2026-06-01")
    except ValueError as e:
        assert "diferentes" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")
