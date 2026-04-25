"""Testes de total_despesa_mes (livro-caixa + cartão, sem dupla fatura)."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.models.payment import Payment
from app.services import expense_totals_service, payments_service


def _seed_account() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta E', 5000.0)"
        )
        return int(cur.lastrowid)


def _seed_card(account_id: int) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO cards (nome, account_id, dia_pagamento_fatura) VALUES ('Visa E', ?, 10)",
            (account_id,),
        )
        return int(cur.lastrowid)


def test_total_despesa_mes_vazio(test_db_path: Path) -> None:
    assert expense_totals_service.total_despesa_mes("2026-08") == 0.0


def test_total_despesa_mes_conta_e_cartao(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = _seed_card(aid)
    payments_service.create(
        Payment(
            id=None,
            valor=80.0,
            descricao="Débito",
            data="2026-09-05",
            conta_id=aid,
            forma_pagamento="Pix",
        ),
        record_ledger=True,
    )
    payments_service.create(
        Payment(
            id=None,
            valor=120.0,
            descricao="Loja",
            data="2026-09-20",
            conta_id=None,
            forma_pagamento="Crédito",
            cartao_id=cid,
        ),
    )
    total = expense_totals_service.total_despesa_mes("2026-09")
    assert total == 200.0


def test_total_despesa_mes_exclui_origem_fatura_no_caixa(test_db_path: Path) -> None:
    """Compra no cartão entra em payments; débito de fatura na conta não soma no caixa."""
    aid = _seed_account()
    cid = _seed_card(aid)
    payments_service.create(
        Payment(
            id=None,
            valor=50.0,
            descricao="Compra cartão",
            data="2026-10-02",
            conta_id=None,
            forma_pagamento="Crédito",
            cartao_id=cid,
        ),
    )
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (?, '2026-10-28', -50.0, 'fatura', 'test:fatura:1', 'Fatura')
            """,
            (aid,),
        )
    total = expense_totals_service.total_despesa_mes("2026-10")
    assert total == 50.0


def test_total_despesa_mes_exclui_ajuste_no_caixa(test_db_path: Path) -> None:
    aid = _seed_account()
    payments_service.create(
        Payment(
            id=None,
            valor=40.0,
            descricao="Pix",
            data="2026-11-03",
            conta_id=aid,
            forma_pagamento="Pix",
        ),
        record_ledger=True,
    )
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (?, '2026-11-03', -500.0, 'ajuste', 'adjustment:test1', 'Conciliação')
            """,
            (aid,),
        )
    assert expense_totals_service.total_despesa_mes("2026-11") == 40.0
