"""Previsto não soma pagamento em conta já debitado no livro-caixa."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.services import accounts_service, dashboard_service


def test_previsto_excludes_payment_already_in_ledger(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta A', 1000)"
        )
        conn.execute(
            """
            INSERT INTO payments (valor, descricao, data, conta_id, forma_pagamento)
            VALUES (50.0, 'Teste', '2026-04-15', 1, 'Pix')
            """
        )
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (1, '2026-04-15', -50.0, 'pagamento', 'payment:1', 'Teste')
            """
        )
    prev = dashboard_service.previsto_mes_for("2026-04")
    assert prev == 0.0
