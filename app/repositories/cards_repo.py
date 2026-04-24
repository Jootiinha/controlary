"""Cartões de crédito."""
from __future__ import annotations

import sqlite3
from typing import List, Optional


_BASE = """
    SELECT c.*, a.nome AS conta_nome
      FROM cards c
      LEFT JOIN accounts a ON a.id = c.account_id
"""


def list_all(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(f"{_BASE} ORDER BY c.nome COLLATE NOCASE").fetchall()


def get(conn: sqlite3.Connection, card_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(f"{_BASE} WHERE c.id = ?", (card_id,)).fetchone()


def insert(
    conn: sqlite3.Connection,
    *,
    nome: str,
    account_id: Optional[int],
    observacao: Optional[str],
    dia_pagamento_fatura: int,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO cards (nome, account_id, observacao, dia_pagamento_fatura)
        VALUES (?, ?, ?, ?)
        """,
        (nome, account_id, observacao, dia_pagamento_fatura),
    )
    return int(cur.lastrowid)


def update(
    conn: sqlite3.Connection,
    *,
    card_id: int,
    nome: str,
    account_id: Optional[int],
    observacao: Optional[str],
    dia_pagamento_fatura: int,
) -> None:
    conn.execute(
        """
        UPDATE cards SET nome = ?, account_id = ?, observacao = ?,
               dia_pagamento_fatura = ?
         WHERE id = ?
        """,
        (nome, account_id, observacao, dia_pagamento_fatura, card_id),
    )


def count_usage(conn: sqlite3.Connection, card_id: int) -> int:
    row = conn.execute(
        """
        SELECT (
            SELECT COUNT(*) FROM installments WHERE cartao_id = ?
        ) + (
            SELECT COUNT(*) FROM subscriptions WHERE card_id = ?
        ) AS n
        """,
        (card_id, card_id),
    ).fetchone()
    return int(row["n"] or 0) if row else 0


def delete(conn: sqlite3.Connection, card_id: int) -> None:
    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
