"""Contas bancárias (tabela ``accounts``)."""
from __future__ import annotations

import sqlite3
from typing import List, Optional


_LIST_SELECT = """
    SELECT a.id, a.nome, a.observacao, a.saldo_inicial,
           a.saldo_inicial + COALESCE((
             SELECT SUM(t.valor)
               FROM account_transactions t
              WHERE t.account_id = a.id
                AND date(t.data) <= date('now', 'localtime')
           ), 0) AS saldo_atual
      FROM accounts a
"""


def list_all(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(f"{_LIST_SELECT} ORDER BY a.nome COLLATE NOCASE").fetchall()


def get(conn: sqlite3.Connection, account_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        f"{_LIST_SELECT} WHERE a.id = ?",
        (account_id,),
    ).fetchone()


def insert(
    conn: sqlite3.Connection,
    *,
    nome: str,
    observacao: Optional[str],
    saldo_inicial: float,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO accounts (nome, observacao, saldo_inicial)
        VALUES (?, ?, ?)
        """,
        (nome, observacao, saldo_inicial),
    )
    return int(cur.lastrowid)


def update(
    conn: sqlite3.Connection,
    *,
    account_id: int,
    nome: str,
    observacao: Optional[str],
    saldo_inicial: float,
) -> None:
    conn.execute(
        """
        UPDATE accounts
           SET nome = ?, observacao = ?, saldo_inicial = ?
         WHERE id = ?
        """,
        (nome, observacao, saldo_inicial, account_id),
    )


def delete(conn: sqlite3.Connection, account_id: int) -> None:
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))


def count_references(conn: sqlite3.Connection, account_id: int) -> int:
    row = conn.execute(
        """
        SELECT (
            SELECT COUNT(*) FROM payments WHERE conta_id = ?
        ) + (
            SELECT COUNT(*) FROM subscriptions WHERE account_id = ?
        ) + (
            SELECT COUNT(*) FROM cards WHERE account_id = ?
        ) + (
            SELECT COUNT(*) FROM fixed_expenses WHERE conta_id = ?
        ) + (
            SELECT COUNT(*) FROM investments WHERE banco_id = ?
        ) + (
            SELECT COUNT(*) FROM income_sources WHERE account_id = ?
        ) + (
            SELECT COUNT(*) FROM installments WHERE account_id = ?
        ) + (
            SELECT COUNT(*) FROM account_transactions WHERE account_id = ?
        ) AS n
        """,
        (
            account_id,
            account_id,
            account_id,
            account_id,
            account_id,
            account_id,
            account_id,
            account_id,
        ),
    ).fetchone()
    return int(row["n"] or 0) if row else 0
