"""CRUD de cartões."""
from __future__ import annotations

from typing import List, Optional

from app.database.connection import transaction
from app.models.card import Card


def list_all() -> List[Card]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT c.*, a.nome AS conta_nome
              FROM cards c
              LEFT JOIN accounts a ON a.id = c.account_id
             ORDER BY c.nome COLLATE NOCASE
            """
        ).fetchall()
    return [Card.from_row(r) for r in rows]


def get(card_id: int) -> Optional[Card]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT c.*, a.nome AS conta_nome
              FROM cards c
              LEFT JOIN accounts a ON a.id = c.account_id
             WHERE c.id = ?
            """,
            (card_id,),
        ).fetchone()
    return Card.from_row(row) if row else None


def create(card: Card) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO cards (nome, account_id, observacao, dia_pagamento_fatura)
            VALUES (?, ?, ?, ?)
            """,
            (
                card.nome.strip(),
                card.account_id,
                card.observacao,
                card.dia_pagamento_fatura,
            ),
        )
        return int(cur.lastrowid)


def update(card: Card) -> None:
    if card.id is None:
        raise ValueError("Cartão sem id")
    with transaction() as conn:
        conn.execute(
            """
            UPDATE cards SET nome = ?, account_id = ?, observacao = ?,
                   dia_pagamento_fatura = ?
             WHERE id = ?
            """,
            (
                card.nome.strip(),
                card.account_id,
                card.observacao,
                card.dia_pagamento_fatura,
                card.id,
            ),
        )


def delete(card_id: int) -> None:
    with transaction() as conn:
        n = conn.execute(
            """
            SELECT (
                SELECT COUNT(*) FROM installments WHERE cartao_id = ?
            ) + (
                SELECT COUNT(*) FROM subscriptions WHERE card_id = ?
            ) AS n
            """,
            (card_id, card_id),
        ).fetchone()
        if n and int(n["n"] or 0) > 0:
            raise ValueError(
                "Este cartão está em uso em parcelamentos ou assinaturas."
            )
        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
