"""Competência mensal de recebimento de renda (livro-caixa)."""
from __future__ import annotations

from calendar import monthrange
from datetime import date

from app.database.connection import transaction
from app.services import accounts_service


def is_received(income_source_id: int, ano_mes: str) -> bool:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT status FROM income_months
             WHERE income_source_id = ? AND ano_mes = ?
            """,
            (income_source_id, ano_mes),
        ).fetchone()
    return row is not None and row["status"] == "recebido"


def set_month_status(income_source_id: int, ano_mes: str, recebido: bool) -> None:
    status = "recebido" if recebido else "pendente"
    key = accounts_service.transaction_key_income(income_source_id, ano_mes)
    with transaction() as conn:
        src = conn.execute(
            """
            SELECT valor_mensal, account_id, dia_recebimento, ativo
              FROM income_sources
             WHERE id = ?
            """,
            (income_source_id,),
        ).fetchone()
        prev_row = conn.execute(
            """
            SELECT status FROM income_months
             WHERE income_source_id = ? AND ano_mes = ?
            """,
            (income_source_id, ano_mes),
        ).fetchone()
        was_rec = prev_row is not None and prev_row["status"] == "recebido"

        if not recebido:
            accounts_service.remove_transaction_key(key, conn=conn)
        elif not was_rec and src and src["account_id"] and src["ativo"]:
            y, m = map(int, ano_mes.split("-"))
            dia = min(int(src["dia_recebimento"] or 5), monthrange(y, m)[1])
            data = f"{y:04d}-{m:02d}-{dia:02d}"
            accounts_service.upsert_transaction(
                int(src["account_id"]),
                float(src["valor_mensal"]),
                data,
                "renda",
                key,
                None,
                conn=conn,
            )

        row = conn.execute(
            """
            SELECT 1 FROM income_months
             WHERE income_source_id = ? AND ano_mes = ?
            """,
            (income_source_id, ano_mes),
        ).fetchone()
        rec_em = date.today().isoformat() if recebido else None
        if row:
            conn.execute(
                """
                UPDATE income_months SET status = ?, recebido_em = ?
                 WHERE income_source_id = ? AND ano_mes = ?
                """,
                (status, rec_em, income_source_id, ano_mes),
            )
        else:
            conn.execute(
                """
                INSERT INTO income_months (income_source_id, ano_mes, status, recebido_em)
                VALUES (?, ?, ?, ?)
                """,
                (income_source_id, ano_mes, status, rec_em),
            )
