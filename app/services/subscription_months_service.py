"""Competência mensal de assinaturas em conta (livro-caixa)."""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.database.connection import use
from app.events import app_events
from app.repositories import subscription_months_repo
from app.services import accounts_service
from app.services._monthly_ledger import MonthlyLedgerService
from app.services.competencia_ledger import data_iso_no_mes
from app.utils.mes_ano import MesAno


def is_paid(
    subscription_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> bool:
    with use(conn) as c:
        st = subscription_months_repo.fetch_month_status(c, subscription_id, ano_mes)
    return st == "pago"


class _SubscriptionMonthLedger(MonthlyLedgerService):
    def set_status(
        self,
        entity_id: int,
        ano_mes: MesAno,
        marcado: bool,
        *,
        conn: Optional[sqlite3.Connection] = None,
        **kwargs: object,
    ) -> None:
        subscription_id = entity_id
        pago = marcado
        ym = str(ano_mes)
        status = "pago" if pago else "pendente"
        key = accounts_service.transaction_key_subscription(subscription_id, ym)
        with use(conn) as c:
            sub = subscription_months_repo.fetch_subscription_ledger_row(c, subscription_id)
            if not pago:
                accounts_service.remove_transaction_key(key, conn=c)
            elif pago and sub and sub["card_id"] is not None:
                raise ValueError(
                    "Assinatura no cartão não usa competência mensal em conta; pague pela fatura."
                )
            elif pago and sub and sub["status"] != "ativa":
                raise ValueError(
                    "Só é possível marcar como pago assinaturas com status «ativa»."
                )
            elif pago and sub and not sub["account_id"]:
                raise ValueError(
                    "Assinatura sem conta: associe uma conta ou use apenas no cartão."
                )
            elif sub and sub["account_id"] and sub["status"] == "ativa":
                dia = int(sub["dia_cobranca"] or 5)
                data = data_iso_no_mes(ym, dia)
                accounts_service.upsert_transaction(
                    int(sub["account_id"]),
                    -float(sub["valor_mensal"]),
                    data,
                    "assinatura",
                    key,
                    None,
                    conn=c,
                )
            subscription_months_repo.upsert_month(
                c, subscription_id, ym, status, pago=pago
            )
        app_events().subscriptions_changed.emit()


_SUB = _SubscriptionMonthLedger()


def set_month_status(
    subscription_id: int,
    ano_mes: str,
    pago: bool,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    _SUB.set_status(subscription_id, MesAno.from_str(ano_mes), pago, conn=conn)
