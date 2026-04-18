"""Competência mensal de parcelamentos em conta corrente (livro-caixa)."""
from __future__ import annotations

from calendar import monthrange
from datetime import date

from app.database.connection import transaction
from app.services import accounts_service


def is_paid(installment_id: int, ano_mes: str) -> bool:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT status FROM installment_months
             WHERE installment_id = ? AND ano_mes = ?
            """,
            (installment_id, ano_mes),
        ).fetchone()
    return row is not None and row["status"] == "pago"


def set_month_status(installment_id: int, ano_mes: str, pago: bool) -> None:
    """Só debita/credita quando o parcelamento é em conta e a competência coincide com mes_referencia."""
    status = "pago" if pago else "pendente"
    key = accounts_service.transaction_key_installment(installment_id, ano_mes)
    with transaction() as conn:
        inst = conn.execute(
            """
            SELECT valor_parcela, account_id, cartao_id, mes_referencia,
                   total_parcelas, parcelas_pagas, status
              FROM installments
             WHERE id = ?
            """,
            (installment_id,),
        ).fetchone()
        if not inst:
            return

        prev_row = conn.execute(
            """
            SELECT status FROM installment_months
             WHERE installment_id = ? AND ano_mes = ?
            """,
            (installment_id, ano_mes),
        ).fetchone()
        was_pago = prev_row is not None and prev_row["status"] == "pago"

        applies = (
            inst["cartao_id"] is None
            and inst["account_id"] is not None
            and inst["mes_referencia"] == ano_mes
            and inst["status"] != "quitado"
        )

        if not applies:
            if not pago:
                accounts_service.remove_transaction_key(key, conn=conn)
            _upsert_month_row(conn, installment_id, ano_mes, status, pago)
            return

        if not pago:
            accounts_service.remove_transaction_key(key, conn=conn)
            if was_pago:
                inst2 = conn.execute(
                    """
                    SELECT parcelas_pagas, total_parcelas FROM installments WHERE id = ?
                    """,
                    (installment_id,),
                ).fetchone()
                if inst2 and int(inst2["parcelas_pagas"] or 0) > 0:
                    novo = int(inst2["parcelas_pagas"]) - 1
                    tot = int(inst2["total_parcelas"])
                    st = "quitado" if novo >= tot else "ativo"
                    conn.execute(
                        """
                        UPDATE installments
                           SET parcelas_pagas = ?, status = ?
                         WHERE id = ?
                        """,
                        (max(0, novo), st, installment_id),
                    )
        elif not was_pago:
            y, m = map(int, ano_mes.split("-"))
            dia = min(15, monthrange(y, m)[1])
            data = f"{y:04d}-{m:02d}-{dia:02d}"
            accounts_service.upsert_transaction(
                int(inst["account_id"]),
                -float(inst["valor_parcela"]),
                data,
                "parcela",
                key,
                None,
                conn=conn,
            )
            inst2 = conn.execute(
                """
                SELECT parcelas_pagas, total_parcelas FROM installments WHERE id = ?
                """,
                (installment_id,),
            ).fetchone()
            if inst2:
                novo = min(
                    int(inst2["parcelas_pagas"] or 0) + 1,
                    int(inst2["total_parcelas"]),
                )
                tot = int(inst2["total_parcelas"])
                st = "quitado" if novo >= tot else "ativo"
                conn.execute(
                    """
                    UPDATE installments
                       SET parcelas_pagas = ?, status = ?
                     WHERE id = ?
                    """,
                    (novo, st, installment_id),
                )

        _upsert_month_row(conn, installment_id, ano_mes, status, pago)


def _upsert_month_row(
    conn,
    installment_id: int,
    ano_mes: str,
    status: str,
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
