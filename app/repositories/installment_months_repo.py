"""SQL para installment_months e atualização de installments no fluxo mensal."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import Optional


def fetch_installment_for_ledger(
    conn: sqlite3.Connection, installment_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT valor_parcela, account_id, cartao_id, mes_referencia,
               total_parcelas, parcelas_pagas, status
          FROM installments
         WHERE id = ?
        """,
        (installment_id,),
    ).fetchone()


def fetch_month_status(
    conn: sqlite3.Connection, installment_id: int, ano_mes: str
) -> Optional[str]:
    row = conn.execute(
        """
        SELECT status FROM installment_months
         WHERE installment_id = ? AND ano_mes = ?
        """,
        (installment_id, ano_mes),
    ).fetchone()
    return str(row["status"]) if row else None


def fetch_parcels_row(
    conn: sqlite3.Connection, installment_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT parcelas_pagas, total_parcelas FROM installments WHERE id = ?
        """,
        (installment_id,),
    ).fetchone()


def update_installment_parcels(
    conn: sqlite3.Connection, installment_id: int, parcelas_pagas: int, status: str
) -> None:
    conn.execute(
        """
        UPDATE installments
           SET parcelas_pagas = ?, status = ?
         WHERE id = ?
        """,
        (parcelas_pagas, status, installment_id),
    )


def upsert_month(
    conn: sqlite3.Connection,
    installment_id: int,
    ano_mes: str,
    status: str,
    *,
    pago: bool,
) -> None:
    row = conn.execute(
        """
        SELECT 1 FROM installment_months
         WHERE installment_id = ? AND ano_mes = ?
        """,
        (installment_id, ano_mes),
    ).fetchone()
    paid_at = date.today().isoformat() if pago else None
    if row:
        conn.execute(
            """
            UPDATE installment_months SET status = ?, paid_at = ?
             WHERE installment_id = ? AND ano_mes = ?
            """,
            (status, paid_at, installment_id, ano_mes),
        )
    else:
        conn.execute(
            """
            INSERT INTO installment_months (installment_id, ano_mes, status, paid_at)
            VALUES (?, ?, ?, ?)
            """,
            (installment_id, ano_mes, status, paid_at),
        )
