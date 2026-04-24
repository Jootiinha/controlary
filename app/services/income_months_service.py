"""Competência mensal de recebimento de renda (livro-caixa)."""
from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Optional

from app.database.connection import transaction
from app.services import accounts_service

_UNSET = object()


def count_received(income_source_id: int, ano_meses) -> int:
    meses = tuple(ano_meses)
    if not meses:
        return 0
    placeholders = ",".join("?" * len(meses))
    with transaction() as conn:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS n FROM income_months
             WHERE income_source_id = ? AND status = 'recebido'
               AND ano_mes IN ({placeholders})
            """,
            (income_source_id, *meses),
        ).fetchone()
    return int(row["n"]) if row else 0


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


def get_month_record(
    income_source_id: int, ano_mes: str
) -> Optional[tuple[bool, Optional[float], Optional[int]]]:
    """(recebido, valor_efetivo, conta_recebimento_id) ou None se não existir linha."""
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT status, valor_efetivo, conta_recebimento_id
              FROM income_months
             WHERE income_source_id = ? AND ano_mes = ?
            """,
            (income_source_id, ano_mes),
        ).fetchone()
    if row is None:
        return None
    rec = row["status"] == "recebido"
    ve: Optional[float] = None
    try:
        raw = row["valor_efetivo"]
        if raw is not None:
            ve = float(raw)
    except (KeyError, TypeError, ValueError):
        ve = None
    cr: Optional[int] = None
    try:
        raw_c = row["conta_recebimento_id"]
        if raw_c is not None:
            cr = int(raw_c)
    except (KeyError, TypeError, ValueError):
        cr = None
    return (rec, ve, cr)


def resolved_account_id(
    src_account_id: Optional[int],
    month_conta_recebimento_id: Optional[int],
) -> Optional[int]:
    if month_conta_recebimento_id is not None:
        return month_conta_recebimento_id
    return src_account_id


def set_month_status(
    income_source_id: int,
    ano_mes: str,
    recebido: bool,
    valor_efetivo: Optional[float] = None,
    conta_recebimento_id: Optional[int] | object = _UNSET,
) -> None:
    status = "recebido" if recebido else "pendente"
    key = accounts_service.transaction_key_income(income_source_id, ano_mes)
    with transaction() as conn:
        src = conn.execute(
            """
            SELECT valor_mensal, account_id, dia_recebimento
              FROM income_sources
             WHERE id = ?
            """,
            (income_source_id,),
        ).fetchone()
        prev_row = conn.execute(
            """
            SELECT status, valor_efetivo, conta_recebimento_id
              FROM income_months
             WHERE income_source_id = ? AND ano_mes = ?
            """,
            (income_source_id, ano_mes),
        ).fetchone()
        prev_ve: Optional[float] = None
        prev_crid: Optional[int] = None
        if prev_row:
            try:
                raw = prev_row["valor_efetivo"]
                if raw is not None:
                    prev_ve = float(raw)
            except (KeyError, TypeError, ValueError):
                prev_ve = None
            try:
                raw_c = prev_row["conta_recebimento_id"]
                if raw_c is not None:
                    prev_crid = int(raw_c)
            except (KeyError, TypeError, ValueError):
                prev_crid = None

        if not recebido:
            accounts_service.remove_transaction_key(key, conn=conn)
        elif recebido and src:
            src_acc: Optional[int] = None
            try:
                if src["account_id"] is not None:
                    src_acc = int(src["account_id"])
            except (KeyError, TypeError, ValueError):
                src_acc = None

            if conta_recebimento_id is _UNSET:
                crid_resolved = prev_crid
            else:
                crid_resolved = int(conta_recebimento_id) if conta_recebimento_id is not None else None  # type: ignore[arg-type]

            acc_id = resolved_account_id(src_acc, crid_resolved)
            if acc_id is not None:
                y, m = map(int, ano_mes.split("-"))
                dia = min(int(src["dia_recebimento"] or 5), monthrange(y, m)[1])
                data = f"{y:04d}-{m:02d}-{dia:02d}"
                if valor_efetivo is not None:
                    cred = float(valor_efetivo)
                elif prev_ve is not None:
                    cred = prev_ve
                else:
                    cred = float(src["valor_mensal"])
                accounts_service.upsert_transaction(
                    acc_id,
                    cred,
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
        ve_store: Optional[float] = None
        crid_store: Optional[int] = None
        if recebido and src:
            if valor_efetivo is not None:
                ve_store = float(valor_efetivo)
            elif prev_ve is not None:
                ve_store = prev_ve
            else:
                ve_store = float(src["valor_mensal"])
            if conta_recebimento_id is _UNSET:
                crid_store = prev_crid
            else:
                crid_store = int(conta_recebimento_id) if conta_recebimento_id is not None else None  # type: ignore[arg-type]
        if row:
            conn.execute(
                """
                UPDATE income_months SET status = ?, recebido_em = ?, valor_efetivo = ?,
                       conta_recebimento_id = ?
                 WHERE income_source_id = ? AND ano_mes = ?
                """,
                (status, rec_em, ve_store, crid_store, income_source_id, ano_mes),
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
                (income_source_id, ano_mes, status, rec_em, ve_store, crid_store),
            )


def delete_rows_not_in(income_source_id: int, keep: set[str]) -> None:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT ano_mes FROM income_months
             WHERE income_source_id = ?
            """,
            (income_source_id,),
        ).fetchall()
        for r in rows:
            ym = r["ano_mes"]
            if ym not in keep:
                key = accounts_service.transaction_key_income(income_source_id, ym)
                accounts_service.remove_transaction_key(key, conn=conn)
                conn.execute(
                    """
                    DELETE FROM income_months
                     WHERE income_source_id = ? AND ano_mes = ?
                    """,
                    (income_source_id, ym),
                )
