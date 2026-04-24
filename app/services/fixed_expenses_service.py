"""Gastos fixos mensais (aluguel, luz etc.) com status pago/pendente por competência."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import List, Optional, Tuple

from app.database.connection import use
from app.events import app_events
from app.models.fixed_expense import FixedExpense
from app.repositories import fixed_expenses_repo
from app.services import accounts_service
from app.services._monthly_ledger import MonthlyLedgerService
from app.services.competencia_ledger import data_iso_no_mes
from app.utils.mes_ano import MesAno


def is_paid(fe_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Sem registro = ainda não pago (previsto)."""
    with use(conn) as c:
        st = fixed_expenses_repo.status_row(c, fe_id, ano_mes)
    return st == "pago"


def get_valor_efetivo(
    fe_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[float]:
    with use(conn) as c:
        return fixed_expenses_repo.fetch_valor_efetivo_month(c, fe_id, ano_mes)


class _FixedExpenseMonthLedger(MonthlyLedgerService):
    def set_status(
        self,
        entity_id: int,
        ano_mes: MesAno,
        marcado: bool,
        *,
        conn: Optional[sqlite3.Connection] = None,
        **kwargs: object,
    ) -> None:
        fe_id = entity_id
        pago = marcado
        ym = str(ano_mes)
        valor_efetivo: Optional[float] = kwargs.get("valor_efetivo")  # type: ignore[assignment]
        conta_debito_id: Optional[int] = kwargs.get("conta_debito_id")  # type: ignore[assignment]
        status = "pago" if pago else "pendente"
        with use(conn) as c:
            fe = fixed_expenses_repo.fetch_fixed_for_month_apply(c, fe_id)
            key = accounts_service.transaction_key_fixed(fe_id, ym)
            valor_debito = (
                float(valor_efetivo)
                if valor_efetivo is not None
                else (float(fe["valor_mensal"]) if fe else 0.0)
            )
            valor_gravado: Optional[float] = None
            if pago and fe:
                valor_gravado = (
                    float(valor_efetivo)
                    if valor_efetivo is not None
                    else float(fe["valor_mensal"])
                )
            effective_conta: Optional[int] = None
            if fe:
                if fe["conta_id"]:
                    effective_conta = int(fe["conta_id"])
                elif conta_debito_id is not None:
                    effective_conta = int(conta_debito_id)
            if not pago:
                accounts_service.remove_transaction_key(key, conn=c)
            elif effective_conta is None:
                raise ValueError(
                    "Marque como pago somente com conta para débito no livro-caixa "
                    "(cadastre conta no fixo ou escolha conta no diálogo)."
                )
            else:
                dia = int(fe["dia_referencia"] or 5) if fe else 5
                data = data_iso_no_mes(ym, dia)
                accounts_service.upsert_transaction(
                    effective_conta,
                    -valor_debito,
                    data,
                    "fixo",
                    key,
                    None,
                    conn=c,
                )
            fixed_expenses_repo.upsert_month_row(c, fe_id, ym, status, valor_gravado)
        app_events().fixed_changed.emit()


_FIX = _FixedExpenseMonthLedger()


def set_month_status(
    fe_id: int,
    ano_mes: str,
    pago: bool,
    valor_efetivo: Optional[float] = None,
    conta_debito_id: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    _FIX.set_status(
        fe_id,
        MesAno.from_str(ano_mes),
        pago,
        conn=conn,
        valor_efetivo=valor_efetivo,
        conta_debito_id=conta_debito_id,
    )


def list_active(conn: Optional[sqlite3.Connection] = None) -> List[FixedExpense]:
    with use(conn) as c:
        rows = fixed_expenses_repo.list_active(c)
    return [FixedExpense.from_row(r) for r in rows]


def list_all(conn: Optional[sqlite3.Connection] = None) -> List[FixedExpense]:
    with use(conn) as c:
        rows = fixed_expenses_repo.list_all(c)
    return [FixedExpense.from_row(r) for r in rows]


def get(fe_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[FixedExpense]:
    with use(conn) as c:
        row = fixed_expenses_repo.get(c, fe_id)
    return FixedExpense.from_row(row) if row else None


def create(fe: FixedExpense, conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        pid = fixed_expenses_repo.insert(
            c,
            nome=fe.nome.strip(),
            valor_mensal=fe.valor_mensal,
            dia_referencia=fe.dia_referencia,
            forma_pagamento=fe.forma_pagamento,
            conta_id=fe.conta_id,
            observacao=fe.observacao,
            ativo=1 if fe.ativo else 0,
            category_id=fe.category_id,
        )
    app_events().fixed_changed.emit()
    return pid


def update(fe: FixedExpense, conn: Optional[sqlite3.Connection] = None) -> None:
    if fe.id is None:
        raise ValueError("Gasto fixo sem id")
    with use(conn) as c:
        fixed_expenses_repo.update(
            c,
            fe_id=int(fe.id),
            nome=fe.nome.strip(),
            valor_mensal=fe.valor_mensal,
            dia_referencia=fe.dia_referencia,
            forma_pagamento=fe.forma_pagamento,
            conta_id=fe.conta_id,
            observacao=fe.observacao,
            ativo=1 if fe.ativo else 0,
            category_id=fe.category_id,
        )
    app_events().fixed_changed.emit()


def delete(fe_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        accounts_service.remove_transaction_keys_like_prefix(
            f"fixed:{fe_id}:", conn=c
        )
        fixed_expenses_repo.delete(c, fe_id)
    app_events().fixed_changed.emit()


def sum_unpaid_for_month(ano_mes: str, conn: Optional[sqlite3.Connection] = None) -> float:
    """Soma valores de itens ativos cuja competência não está como paga."""
    with use(conn) as c:
        rows = fixed_expenses_repo.sum_unpaid_for_month(c, ano_mes)
    total = 0.0
    for r in rows:
        if r["status"] != "pago":
            total += float(r["valor_mensal"] or 0)
    return round(total, 2)


def sum_paid_for_month(ano_mes: str, conn: Optional[sqlite3.Connection] = None) -> float:
    """Soma valores pagos no mês (valor_efetivo quando informado, senão valor_mensal)."""
    with use(conn) as c:
        row = fixed_expenses_repo.sum_paid_for_month_row(c, ano_mes)
    return round(float(row["t"] or 0), 2) if row else 0.0


def sum_unpaid_rest_of_calendar_year() -> float:
    """Soma todos os meses do ano corrente, da competência atual até dezembro, apenas pendências."""
    d = date.today()
    y, m0 = d.year, d.month
    total = 0.0
    for m in range(m0, 13):
        ym = f"{y}-{m:02d}"
        total += sum_unpaid_for_month(ym)
    return round(total, 2)


def projection_by_month_rest_of_year() -> List[Tuple[str, float]]:
    """Lista (YYYY-MM, total pendente) do mês atual até dez/ano."""
    d = date.today()
    y, m0 = d.year, d.month
    out: List[Tuple[str, float]] = []
    for m in range(m0, 13):
        ym = f"{y}-{m:02d}"
        out.append((ym, sum_unpaid_for_month(ym)))
    return out


def count_active(conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        return fixed_expenses_repo.count_active(c)
