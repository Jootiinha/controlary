"""Competência mensal de parcelamentos em conta corrente (livro-caixa)."""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.database.connection import use
from app.events import app_events
from app.models.income_source import competencias_parcelada
from app.models.installment import schedule_parcel_amounts
from app.repositories import installment_months_repo
from app.services import accounts_service
from app.services._monthly_ledger import MonthlyLedgerService
from app.services.competencia_ledger import data_iso_no_mes
from app.utils.mes_ano import MesAno


def is_paid(
    installment_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> bool:
    with use(conn) as c:
        st = installment_months_repo.fetch_month_status(c, installment_id, ano_mes)
    return st == "pago"


class _InstallmentMonthLedger(MonthlyLedgerService):
    def set_status(
        self,
        entity_id: int,
        ano_mes: MesAno,
        marcado: bool,
        *,
        conn: Optional[sqlite3.Connection] = None,
        **kwargs: object,
    ) -> None:
        installment_id = entity_id
        pago = marcado
        ym = str(ano_mes)
        status = "pago" if pago else "pendente"
        key = accounts_service.transaction_key_installment(installment_id, ym)
        with use(conn) as c:
            inst = installment_months_repo.fetch_installment_for_ledger(c, installment_id)
            if not inst:
                return

            mes_ref = inst["mes_referencia"]
            total = int(inst["total_parcelas"] or 0)
            schedule = competencias_parcelada(mes_ref, total) if total > 0 else []
            in_schedule = ym in schedule
            slot_idx = schedule.index(ym) if in_schedule else -1

            prev_st = installment_months_repo.fetch_month_status(
                c, installment_id, ym
            )
            was_pago = prev_st == "pago"

            pagas = int(inst["parcelas_pagas"] or 0)

            base = (
                inst["cartao_id"] is None
                and inst["account_id"] is not None
                and in_schedule
                and inst["status"] != "quitado"
            )

            if not base:
                if not pago:
                    accounts_service.remove_transaction_key(key, conn=c)
                installment_months_repo.upsert_month(
                    c, installment_id, ym, status, pago=pago
                )
                app_events().installments_changed.emit()
                return

            if pago:
                if was_pago:
                    installment_months_repo.upsert_month(
                        c, installment_id, ym, status, pago=pago
                    )
                    app_events().installments_changed.emit()
                    return
                if pagas != slot_idx:
                    installment_months_repo.upsert_month(
                        c, installment_id, ym, "pendente", pago=False
                    )
                    app_events().installments_changed.emit()
                    return
                data = data_iso_no_mes(ym, 15)
                n_par = int(inst["total_parcelas"] or 0)
                vp = float(inst["valor_parcela"] or 0)
                total_contrato = round(vp * n_par, 2) if n_par > 0 else 0.0
                amounts = schedule_parcel_amounts(total_contrato, n_par)
                parcela_valor = (
                    amounts[slot_idx]
                    if 0 <= slot_idx < len(amounts)
                    else vp
                )
                accounts_service.upsert_transaction(
                    int(inst["account_id"]),
                    -parcela_valor,
                    data,
                    "parcela",
                    key,
                    None,
                    conn=c,
                )
                inst2 = installment_months_repo.fetch_parcels_row(c, installment_id)
                if inst2:
                    novo = min(
                        int(inst2["parcelas_pagas"] or 0) + 1,
                        int(inst2["total_parcelas"]),
                    )
                    tot = int(inst2["total_parcelas"])
                    st_inst = "quitado" if novo >= tot else "ativo"
                    installment_months_repo.update_installment_parcels(
                        c, installment_id, novo, st_inst
                    )

                installment_months_repo.upsert_month(
                    c, installment_id, ym, status, pago=pago
                )
                app_events().installments_changed.emit()
                return

            accounts_service.remove_transaction_key(key, conn=c)
            if was_pago and pagas == slot_idx + 1:
                inst2 = installment_months_repo.fetch_parcels_row(c, installment_id)
                if inst2 and int(inst2["parcelas_pagas"] or 0) > 0:
                    novo = int(inst2["parcelas_pagas"] or 0) - 1
                    tot = int(inst2["total_parcelas"])
                    st_inst = "quitado" if novo >= tot else "ativo"
                    installment_months_repo.update_installment_parcels(
                        c, installment_id, max(0, novo), st_inst
                    )

            installment_months_repo.upsert_month(
                c, installment_id, ym, status, pago=pago
            )
        app_events().installments_changed.emit()


_INS = _InstallmentMonthLedger()


def set_month_status(
    installment_id: int, ano_mes: str, pago: bool, conn: Optional[sqlite3.Connection] = None
) -> None:
    _INS.set_status(installment_id, MesAno.from_str(ano_mes), pago, conn=conn)
