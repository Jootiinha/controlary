"""Testes de CRUD de assinaturas e totais."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.subscription import Subscription
from app.services import (
    accounts_service,
    subscription_months_service,
    subscriptions_service,
)


def _seed_account() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta S', 500.0)"
        )
        return int(cur.lastrowid)


def _seed_card(account_id: int) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO cards (nome, account_id, dia_pagamento_fatura) VALUES ('Master', ?, 12)",
            (account_id,),
        )
        return int(cur.lastrowid)


def test_create_get_list_total_active(test_db_path: Path) -> None:
    aid = _seed_account()
    sid = subscriptions_service.create(
        Subscription(
            id=None,
            nome="Streaming",
            categoria=None,
            valor_mensal=39.9,
            dia_cobranca=10,
            forma_pagamento="Débito",
            account_id=aid,
            card_id=None,
        )
    )
    sub = subscriptions_service.get(sid)
    assert sub is not None
    assert sub.nome == "Streaming"
    assert sub.meio_label == "Conta S"
    assert sub.valor_mensal == 39.9

    all_subs = subscriptions_service.list_all()
    assert len(all_subs) == 1
    qtd, total = subscriptions_service.total_active()
    assert qtd == 1
    assert total == 39.9
    assert subscriptions_service.sum_active_not_on_card() == 39.9


def test_sum_active_not_on_card_excludes_cartao(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = _seed_card(aid)
    subscriptions_service.create(
        Subscription(
            id=None,
            nome="Só conta",
            categoria=None,
            valor_mensal=10.0,
            dia_cobranca=1,
            forma_pagamento="Pix",
            account_id=aid,
        )
    )
    subscriptions_service.create(
        Subscription(
            id=None,
            nome="No cartão",
            categoria=None,
            valor_mensal=20.0,
            dia_cobranca=5,
            forma_pagamento="Crédito",
            card_id=cid,
        )
    )
    assert subscriptions_service.sum_active_not_on_card() == 10.0


def test_delete_removes_subscription_and_ledger_prefix(test_db_path: Path) -> None:
    aid = _seed_account()
    sid = subscriptions_service.create(
        Subscription(
            id=None,
            nome="Box",
            categoria=None,
            valor_mensal=15.0,
            dia_cobranca=3,
            forma_pagamento="Pix",
            account_id=aid,
        )
    )
    subscription_months_service.set_month_status(sid, "2026-04", True)
    key = accounts_service.transaction_key_subscription(sid, "2026-04")
    with transaction() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM account_transactions WHERE transaction_key = ?",
            (key,),
        ).fetchone()[0]
    assert int(n) == 1

    subscriptions_service.delete(sid)
    assert subscriptions_service.get(sid) is None
    with transaction() as conn:
        n2 = conn.execute(
            "SELECT COUNT(*) FROM account_transactions WHERE transaction_key = ?",
            (key,),
        ).fetchone()[0]
    assert int(n2) == 0


def test_update_sem_id_raises(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="sem id"):
        subscriptions_service.update(
            Subscription(
                id=None,
                nome="x",
                categoria=None,
                valor_mensal=1.0,
                dia_cobranca=1,
                forma_pagamento="Pix",
                account_id=_seed_account(),
            )
        )
