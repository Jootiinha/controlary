"""Competência mensal de recebimento de renda (livro-caixa)."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Optional

from app.database.connection import use
from app.events import app_events
from app.repositories import income_months_repo
from app.services import accounts_service
from app.services._monthly_ledger import MonthlyLedgerService
from app.services.competencia_ledger import data_iso_no_mes
from app.utils.mes_ano import MesAno

_UNSET = object()


def count_received(
    income_source_id: int, ano_meses, conn: Optional[sqlite3.Connection] = None
) -> int:
    meses = tuple(str(m) for m in ano_meses)
    with use(conn) as c:
        return income_months_repo.count_received_in_months(c, income_source_id, meses)


def is_received(
    income_source_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> bool:
    with use(conn) as c:
        row = income_months_repo.fetch_month_detail_row(c, income_source_id, ano_mes)
    return row is not None and row["status"] == "recebido"


def get_month_record(
    income_source_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[tuple[bool, Optional[float], Optional[int]]]:
    """(recebido, valor_efetivo, conta_recebimento_id) ou None se não existir linha."""
    with use(conn) as c:
        row = income_months_repo.fetch_month_detail_row(c, income_source_id, ano_mes)
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


class _IncomeMonthLedger(MonthlyLedgerService):
    def set_status(
        self,
        entity_id: int,
        ano_mes: MesAno,
        marcado: bool,
        *,
        conn: Optional[sqlite3.Connection] = None,
        **kwargs: Any,
    ) -> None:
        income_source_id = entity_id
        recebido = marcado
        ym = str(ano_mes)
        valor_efetivo: Optional[float] = kwargs.get("valor_efetivo")
        conta_recebimento_id: Any = kwargs.get("conta_recebimento_id", _UNSET)

        status = "recebido" if recebido else "pendente"
        key = accounts_service.transaction_key_income(income_source_id, ym)
        with use(conn) as c:
            src = income_months_repo.fetch_source_ledger_row(c, income_source_id)
            prev_row = income_months_repo.fetch_month_detail_row(c, income_source_id, ym)
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
                accounts_service.remove_transaction_key(key, conn=c)
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
                    crid_resolved = (
                        int(conta_recebimento_id)
                        if conta_recebimento_id is not None
                        else None
                    )

                acc_id = resolved_account_id(src_acc, crid_resolved)
                if acc_id is not None:
                    dia = int(src["dia_recebimento"] or 5)
                    data = data_iso_no_mes(ym, dia)
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
                        conn=c,
                    )

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
                    crid_store = (
                        int(conta_recebimento_id)
                        if conta_recebimento_id is not None
                        else None
                    )
            income_months_repo.upsert_income_month(
                c,
                income_source_id,
                ym,
                status,
                rec_em,
                ve_store,
                crid_store,
            )
            income_months_repo.refresh_parcelas_recebidas(c, income_source_id)
        app_events().income_changed.emit()


_INC = _IncomeMonthLedger()


def set_month_status(
    income_source_id: int,
    ano_mes: str,
    recebido: bool,
    valor_efetivo: Optional[float] = None,
    conta_recebimento_id: Optional[int] | object = _UNSET,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    kw: dict[str, Any] = {"valor_efetivo": valor_efetivo}
    if conta_recebimento_id is not _UNSET:
        kw["conta_recebimento_id"] = conta_recebimento_id
    _INC.set_status(
        income_source_id,
        MesAno.from_str(ano_mes),
        recebido,
        conn=conn,
        **kw,
    )


def delete_rows_not_in(
    income_source_id: int, keep: set[str], conn: Optional[sqlite3.Connection] = None
) -> None:
    with use(conn) as c:
        for ym in income_months_repo.list_ano_meses_for_source(c, income_source_id):
            if ym not in keep:
                key = accounts_service.transaction_key_income(income_source_id, ym)
                accounts_service.remove_transaction_key(key, conn=c)
                income_months_repo.delete_month_row(c, income_source_id, ym)
        income_months_repo.refresh_parcelas_recebidas(c, income_source_id)
    app_events().income_changed.emit()
