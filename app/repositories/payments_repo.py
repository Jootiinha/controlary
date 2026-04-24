"""Consultas e mutações na tabela ``payments``."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import List, Optional


_BASE_SELECT = """
    SELECT p.*, a.nome AS conta_nome, c.nome AS cartao_nome, cat.nome AS categoria_nome
      FROM payments p
      LEFT JOIN accounts a ON a.id = p.conta_id
      LEFT JOIN cards c ON c.id = p.cartao_id
      LEFT JOIN categories cat ON cat.id = p.category_id
"""


def list_all(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        f"{_BASE_SELECT} ORDER BY date(p.data) DESC, p.id DESC"
    ).fetchall()


def list_between(conn: sqlite3.Connection, data_ini: date, data_fim: date) -> List[sqlite3.Row]:
    s_ini = data_ini.isoformat()
    s_fim = data_fim.isoformat()
    return conn.execute(
        f"{_BASE_SELECT} WHERE date(p.data) BETWEEN date(?) AND date(?)"
        " ORDER BY date(p.data), p.id",
        (s_ini, s_fim),
    ).fetchall()


def get(conn: sqlite3.Connection, payment_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        f"{_BASE_SELECT} WHERE p.id = ?",
        (payment_id,),
    ).fetchone()


def fetch_account_nome(conn: sqlite3.Connection, account_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT nome FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()


def fetch_card_nome(conn: sqlite3.Connection, card_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT nome FROM cards WHERE id = ?", (card_id,)).fetchone()


def insert_account_payment(
    conn: sqlite3.Connection,
    *,
    valor: float,
    descricao: str,
    data: str,
    conta_txt: str,
    conta_id: int,
    forma_pagamento: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO payments (
            valor, descricao, data, conta, conta_id, cartao_id,
            forma_pagamento, observacao, category_id
        ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
        """,
        (
            valor,
            descricao,
            data,
            conta_txt,
            conta_id,
            forma_pagamento,
            observacao,
            category_id,
        ),
    )
    return int(cur.lastrowid)


def insert_card_payment(
    conn: sqlite3.Connection,
    *,
    valor: float,
    descricao: str,
    data: str,
    nome_card: str,
    cartao_id: int,
    forma_pagamento: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO payments (
            valor, descricao, data, conta, conta_id, cartao_id,
            forma_pagamento, observacao, category_id
        ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?)
        """,
        (
            valor,
            descricao,
            data,
            nome_card,
            cartao_id,
            forma_pagamento,
            observacao,
            category_id,
        ),
    )
    return int(cur.lastrowid)


def fetch_prev_origins(conn: sqlite3.Connection, payment_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT conta_id, cartao_id FROM payments WHERE id = ?",
        (payment_id,),
    ).fetchone()


def has_transaction_key(conn: sqlite3.Connection, transaction_key: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM account_transactions WHERE transaction_key = ?",
        (transaction_key,),
    ).fetchone()
    return row is not None


def update_account_payment(
    conn: sqlite3.Connection,
    *,
    valor: float,
    descricao: str,
    data: str,
    nome_conta: str,
    conta_id: int,
    forma_pagamento: str,
    observacao: Optional[str],
    category_id: Optional[int],
    payment_id: int,
) -> None:
    conn.execute(
        """
        UPDATE payments
           SET valor = ?, descricao = ?, data = ?, conta = ?, conta_id = ?,
               cartao_id = NULL, forma_pagamento = ?, observacao = ?, category_id = ?
         WHERE id = ?
        """,
        (
            valor,
            descricao,
            data,
            nome_conta,
            conta_id,
            forma_pagamento,
            observacao,
            category_id,
            payment_id,
        ),
    )


def update_card_payment(
    conn: sqlite3.Connection,
    *,
    valor: float,
    descricao: str,
    data: str,
    nome_card: str,
    cartao_id: int,
    forma_pagamento: str,
    observacao: Optional[str],
    category_id: Optional[int],
    payment_id: int,
) -> None:
    conn.execute(
        """
        UPDATE payments
           SET valor = ?, descricao = ?, data = ?, conta = ?, conta_id = NULL,
               cartao_id = ?, forma_pagamento = ?, observacao = ?, category_id = ?
         WHERE id = ?
        """,
        (
            valor,
            descricao,
            data,
            nome_card,
            cartao_id,
            forma_pagamento,
            observacao,
            category_id,
            payment_id,
        ),
    )


def delete_by_id(conn: sqlite3.Connection, payment_id: int) -> None:
    conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))


def select_mirror_payment_ids(conn: sqlite3.Connection, descricao: str) -> List[int]:
    rows = conn.execute(
        """
        SELECT id FROM payments
         WHERE descricao = ?
           AND cartao_id IS NULL
        """,
        (descricao,),
    ).fetchall()
    return [int(r["id"]) for r in rows]
