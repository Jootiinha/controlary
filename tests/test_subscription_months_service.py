"""Testes de competência mensal de assinaturas (livro-caixa em conta)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.subscription import Subscription
from app.services import accounts_service, subscription_months_service, subscriptions_service


def _seed_account() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta M', 1000.0)"
        )
        return int(cur.lastrowid)


def _seed_card(account_id: int) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO cards (nome, account_id, dia_pagamento_fatura) VALUES ('Card M', ?, 10)",
            (account_id,),
        )
        return int(cur.lastrowid)


def _ledger_for_sub_month(sub_id: int, ano_mes: str) -> list:
    key = accounts_service.transaction_key_subscription(sub_id, ano_mes)
    with transaction() as conn:
        rows = conn.execute(
            "SELECT valor, origem FROM account_transactions WHERE transaction_key = ?",
            (key,),
        ).fetchall()
    return [dict(r) for r in rows]


def test_set_month_pago_conta_cria_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    sid = subscriptions_service.create(
        Subscription(
            id=None,
            nome="App",
            categoria=None,
            valor_mensal=12.0,
            dia_cobranca=15,
            forma_pagamento="Pix",
            account_id=aid,
        )
    )
    subscription_months_service.set_month_status(sid, "2026-04", True)
    assert subscription_months_service.is_paid(sid, "2026-04")
    rows = _ledger_for_sub_month(sid, "2026-04")
    assert len(rows) == 1
    assert rows[0]["valor"] == -12.0
    assert rows[0]["origem"] == "assinatura"


def test_set_month_pago_false_remove_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    sid = subscriptions_service.create(
        Subscription(
            id=None,
            nome="Revista",
            categoria=None,
            valor_mensal=8.0,
            dia_cobranca=1,
            forma_pagamento="Pix",
            account_id=aid,
        )
    )
    subscription_months_service.set_month_status(sid, "2026-05", True)
    assert _ledger_for_sub_month(sid, "2026-05")
    subscription_months_service.set_month_status(sid, "2026-05", False)
    assert not subscription_months_service.is_paid(sid, "2026-05")
    assert _ledger_for_sub_month(sid, "2026-05") == []


def test_set_month_pago_cartao_rejeitado(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = _seed_card(aid)
    sid = subscriptions_service.create(
        Subscription(
            id=None,
            nome="Só crédito",
            categoria=None,
            valor_mensal=50.0,
            dia_cobranca=20,
            forma_pagamento="Crédito",
            card_id=cid,
        )
    )
    with pytest.raises(ValueError):
        subscription_months_service.set_month_status(sid, "2026-04", True)
    assert not subscription_months_service.is_paid(sid, "2026-04")
    assert _ledger_for_sub_month(sid, "2026-04") == []


def test_set_month_pago_pausada_rejeitado(test_db_path: Path) -> None:
    aid = _seed_account()
    sid = subscriptions_service.create(
        Subscription(
            id=None,
            nome="Pausada",
            categoria=None,
            valor_mensal=20.0,
            dia_cobranca=5,
            forma_pagamento="Pix",
            account_id=aid,
            status="pausada",
        )
    )
    with pytest.raises(ValueError):
        subscription_months_service.set_month_status(sid, "2026-06", True)
    assert not subscription_months_service.is_paid(sid, "2026-06")
    assert _ledger_for_sub_month(sid, "2026-06") == []
