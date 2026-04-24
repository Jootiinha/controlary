"""CRUD de cartões."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.database.connection import use
from app.events import app_events
from app.models.card import Card
from app.repositories import cards_repo


def list_all(conn: Optional[sqlite3.Connection] = None) -> List[Card]:
    with use(conn) as c:
        rows = cards_repo.list_all(c)
    return [Card.from_row(r) for r in rows]


def get(card_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Card]:
    with use(conn) as c:
        row = cards_repo.get(c, card_id)
    return Card.from_row(row) if row else None


def get_or_unknown(
    card_id: Optional[int], label: str = "—", conn: Optional[sqlite3.Connection] = None
) -> Card:
    if card_id is None:
        return Card.unknown(label)
    card = get(card_id, conn=conn)
    return card if card is not None else Card.unknown(label)


def create(card: Card, conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        pid = cards_repo.insert(
            c,
            nome=card.nome.strip(),
            account_id=card.account_id,
            observacao=card.observacao,
            dia_pagamento_fatura=card.dia_pagamento_fatura,
        )
    app_events().accounts_changed.emit()
    return pid


def update(card: Card, conn: Optional[sqlite3.Connection] = None) -> None:
    if card.id is None:
        raise ValueError("Cartão sem id")
    with use(conn) as c:
        cards_repo.update(
            c,
            card_id=int(card.id),
            nome=card.nome.strip(),
            account_id=card.account_id,
            observacao=card.observacao,
            dia_pagamento_fatura=card.dia_pagamento_fatura,
        )
    app_events().accounts_changed.emit()


def delete(card_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        if cards_repo.count_usage(c, card_id) > 0:
            raise ValueError(
                "Este cartão está em uso em parcelamentos ou assinaturas."
            )
        cards_repo.delete(c, card_id)
    app_events().accounts_changed.emit()
