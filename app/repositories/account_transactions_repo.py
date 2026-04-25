"""Movimentações do livro-caixa (``account_transactions``)."""
from __future__ import annotations

import sqlite3
from typing import Optional


def account_exists(conn: sqlite3.Connection, account_id: int) -> bool:
    row = conn.execute(
        "SELECT id FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    return row is not None


def delete_by_key(conn: sqlite3.Connection, transaction_key: str) -> None:
    conn.execute(
        "DELETE FROM account_transactions WHERE transaction_key = ?",
        (transaction_key,),
    )


def delete_keys_like_prefix(conn: sqlite3.Connection, prefix: str) -> None:
    conn.execute(
        "DELETE FROM account_transactions WHERE transaction_key LIKE ?",
        (prefix + "%",),
    )


def insert_transaction(
    conn: sqlite3.Connection,
    *,
    account_id: int,
    data: str,
    valor: float,
    origem: str,
    transaction_key: str,
    descricao: Optional[str],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO account_transactions (
            account_id, data, valor, origem, transaction_key, descricao
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (account_id, data, valor, origem, transaction_key, descricao),
    )
    return int(cur.lastrowid)


def sum_for_account_until_today(conn: sqlite3.Connection, account_id: int) -> float:
    r2 = conn.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS t
          FROM account_transactions
         WHERE account_id = ?
           AND date(data) <= date('now', 'localtime')
        """,
        (account_id,),
    ).fetchone()
    return float(r2["t"] or 0)


def fetch_saldo_inicial(conn: sqlite3.Connection, account_id: int) -> Optional[float]:
    row = conn.execute(
        "SELECT saldo_inicial FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    if not row:
        return None
    return float(row["saldo_inicial"] or 0)


def list_account_ids(conn: sqlite3.Connection) -> list[int]:
    rows = conn.execute("SELECT id FROM accounts").fetchall()
    return [int(r["id"]) for r in rows]


def sum_debits_in_month(conn: sqlite3.Connection, ano_mes: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS t
          FROM account_transactions
         WHERE substr(data, 1, 7) = ?
           AND valor < 0
           AND NOT (
               COALESCE(origem, '') = 'ajuste'
               OR COALESCE(transaction_key, '') LIKE 'adjustment:%'
           )
        """,
        (ano_mes,),
    ).fetchone()
    return float(row["t"] or 0)
