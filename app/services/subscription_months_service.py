"""Competência mensal de assinaturas em conta (livro-caixa)."""
from __future__ import annotations

from calendar import monthrange
from datetime import date

from app.database.connection import transaction
from app.services import accounts_service


def is_paid(subscription_id: int, ano_mes: str) -> bool:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT status FROM subscription_months
             WHERE subscription_id = ? AND ano_mes = ?
            """,
            (subscription_id, ano_mes),
        ).fetchone()
    return row is not None and row["status"] == "pago"


def set_month_status(subscription_id: int, ano_mes: str, pago: bool) -> None:
    status = "pago" if pago else "pendente"
    key = accounts_service.transaction_key_subscription(subscription_id, ano_mes)
    with transaction() as conn:
        sub = conn.execute(
            """
            SELECT valor_mensal, account_id, status, dia_cobranca
              FROM subscriptions
             WHERE id = ?
            """,
            (subscription_id,),
        ).fetchone()
        if not pago:
            accounts_service.remove_transaction_key(key, conn=conn)
        elif sub and sub["account_id"] and sub["status"] == "ativa":
            y, m = map(int, ano_mes.split("-"))
            dia = min(int(sub["dia_cobranca"] or 5), monthrange(y, m)[1])
            data = f"{y:04d}-{m:02d}-{dia:02d}"
            accounts_service.upsert_transaction(
                int(sub["account_id"]),
                -float(sub["valor_mensal"]),
                data,
                "assinatura",
                key,
                None,
                conn=conn,
            )
        row = conn.execute(
            """
            SELECT 1 FROM subscription_months
             WHERE subscription_id = ? AND ano_mes = ?
            """,
            (subscription_id, ano_mes),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE subscription_months SET status = ?, paid_at = ?
                 WHERE subscription_id = ? AND ano_mes = ?
                """,
                (
                    status,
                    date.today().isoformat() if pago else None,
                    subscription_id,
                    ano_mes,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO subscription_months (subscription_id, ano_mes, status, paid_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    subscription_id,
                    ano_mes,
                    status,
                    date.today().isoformat() if pago else None,
                ),
            )
