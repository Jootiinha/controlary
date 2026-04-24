"""SQL para income_months e contagens ligadas a income_sources parceladas."""
from __future__ import annotations

import sqlite3
from typing import Optional


def count_received_in_months(
    conn: sqlite3.Connection, income_source_id: int, ano_meses: tuple[str, ...]
) -> int:
    if not ano_meses:
        return 0
    ph = ",".join("?" * len(ano_meses))
    row = conn.execute(
        f"""
        SELECT COUNT(*) AS n FROM income_months
         WHERE income_source_id = ? AND status = 'recebido'
           AND ano_mes IN ({ph})
        """,
        (income_source_id, *ano_meses),
    ).fetchone()
    return int(row["n"]) if row else 0


def fetch_month_status_row(
    conn: sqlite3.Connection, income_source_id: int, ano_mes: str
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT status FROM income_months
         WHERE income_source_id = ? AND ano_mes = ?
        """,
        (income_source_id, ano_mes),
    ).fetchone()


def fetch_month_detail_row(
    conn: sqlite3.Connection, income_source_id: int, ano_mes: str
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT status, valor_efetivo, conta_recebimento_id
          FROM income_months
         WHERE income_source_id = ? AND ano_mes = ?
        """,
        (income_source_id, ano_mes),
    ).fetchone()


def fetch_source_ledger_row(
    conn: sqlite3.Connection, income_source_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT valor_mensal, account_id, dia_recebimento
          FROM income_sources
         WHERE id = ?
        """,
        (income_source_id,),
    ).fetchone()


def income_month_exists(
    conn: sqlite3.Connection, income_source_id: int, ano_mes: str
) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM income_months
         WHERE income_source_id = ? AND ano_mes = ?
        """,
        (income_source_id, ano_mes),
    ).fetchone()
    return row is not None


def upsert_income_month(
    conn: sqlite3.Connection,
    income_source_id: int,
    ano_mes: str,
    status: str,
    recebido_em: Optional[str],
    valor_efetivo: Optional[float],
    conta_recebimento_id: Optional[int],
) -> None:
    if income_month_exists(conn, income_source_id, ano_mes):
        conn.execute(
            """
            UPDATE income_months SET status = ?, recebido_em = ?, valor_efetivo = ?,
                   conta_recebimento_id = ?
             WHERE income_source_id = ? AND ano_mes = ?
            """,
            (
                status,
                recebido_em,
                valor_efetivo,
                conta_recebimento_id,
                income_source_id,
                ano_mes,
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO income_months (
                income_source_id, ano_mes, status, recebido_em, valor_efetivo,
                conta_recebimento_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                income_source_id,
                ano_mes,
                status,
                recebido_em,
                valor_efetivo,
                conta_recebimento_id,
            ),
        )


def refresh_parcelas_recebidas(conn: sqlite3.Connection, income_source_id: int) -> None:
    conn.execute(
        """
        UPDATE income_sources SET parcelas_recebidas = (
            SELECT COUNT(*) FROM income_months
             WHERE income_source_id = ?
               AND status = 'recebido'
        ) WHERE id = ? AND tipo = 'parcelada'
        """,
        (income_source_id, income_source_id),
    )


def list_ano_meses_for_source(
    conn: sqlite3.Connection, income_source_id: int
) -> list[str]:
    rows = conn.execute(
        """
        SELECT ano_mes FROM income_months
         WHERE income_source_id = ?
        """,
        (income_source_id,),
    ).fetchall()
    return [str(r["ano_mes"]) for r in rows]


def delete_month_row(
    conn: sqlite3.Connection, income_source_id: int, ano_mes: str
) -> None:
    conn.execute(
        """
        DELETE FROM income_months
         WHERE income_source_id = ? AND ano_mes = ?
        """,
        (income_source_id, ano_mes),
    )
