"""SQL para subscription_months e leitura mínima de subscriptions (ledger)."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import Optional


def fetch_subscription_ledger_row(
    conn: sqlite3.Connection, subscription_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT valor_mensal, account_id, status, dia_cobranca, card_id
          FROM subscriptions
         WHERE id = ?
        """,
        (subscription_id,),
    ).fetchone()


def fetch_month_status(
    conn: sqlite3.Connection, subscription_id: int, ano_mes: str
) -> Optional[str]:
    row = conn.execute(
        """
        SELECT status FROM subscription_months
         WHERE subscription_id = ? AND ano_mes = ?
        """,
        (subscription_id, ano_mes),
    ).fetchone()
    return str(row["status"]) if row else None


def month_row_exists(
    conn: sqlite3.Connection, subscription_id: int, ano_mes: str
) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM subscription_months
         WHERE subscription_id = ? AND ano_mes = ?
        """,
        (subscription_id, ano_mes),
    ).fetchone()
    return row is not None


def upsert_month(
    conn: sqlite3.Connection,
    subscription_id: int,
    ano_mes: str,
    status: str,
    *,
    pago: bool,
) -> None:
    paid_at = date.today().isoformat() if pago else None
    if month_row_exists(conn, subscription_id, ano_mes):
        conn.execute(
            """
            UPDATE subscription_months SET status = ?, paid_at = ?
             WHERE subscription_id = ? AND ano_mes = ?
            """,
            (status, paid_at, subscription_id, ano_mes),
        )
    else:
        conn.execute(
            """
            INSERT INTO subscription_months (subscription_id, ano_mes, status, paid_at)
            VALUES (?, ?, ?, ?)
            """,
            (subscription_id, ano_mes, status, paid_at),
        )
