"""Testes de CRUD de cartões."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.card import Card
from app.models.subscription import Subscription
from app.services import cards_service, subscriptions_service


def _seed_account() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta C', 0)"
        )
        return int(cur.lastrowid)


def test_create_get_list_update(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = cards_service.create(
        Card(
            id=None,
            nome="  Gold  ",
            account_id=aid,
            observacao="chip",
            dia_pagamento_fatura=21,
        )
    )
    c = cards_service.get(cid)
    assert c is not None
    assert c.nome == "Gold"
    assert c.conta_nome == "Conta C"
    assert c.dia_pagamento_fatura == 21
    cards_service.update(
        Card(
            id=cid,
            nome="Gold",
            account_id=aid,
            observacao="contactless",
            dia_pagamento_fatura=22,
        )
    )
    c2 = cards_service.get(cid)
    assert c2 is not None
    assert c2.observacao == "contactless"
    assert c2.dia_pagamento_fatura == 22
    assert len(cards_service.list_all()) == 1


def test_delete_livre(test_db_path: Path) -> None:
    cid = cards_service.create(
        Card(id=None, nome="Solo", account_id=None, dia_pagamento_fatura=10)
    )
    cards_service.delete(cid)
    assert cards_service.get(cid) is None


def test_delete_em_uso_raises(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = cards_service.create(
        Card(id=None, nome="Vinculado", account_id=aid, dia_pagamento_fatura=10)
    )
    subscriptions_service.create(
        Subscription(
            id=None,
            nome="Serviço",
            categoria=None,
            valor_mensal=9.99,
            dia_cobranca=1,
            forma_pagamento="Crédito",
            card_id=cid,
        )
    )
    with pytest.raises(ValueError, match="parcelamentos ou assinaturas"):
        cards_service.delete(cid)


def test_update_sem_id_raises(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="sem id"):
        cards_service.update(
            Card(id=None, nome="x", dia_pagamento_fatura=10)
        )
