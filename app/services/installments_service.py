"""Operações sobre parcelamentos com cálculo automático de status."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.database.connection import use
from app.events import app_events
from app.models.installment import Installment, schedule_parcel_amounts
from app.repositories import installments_repo
from app.services import accounts_service
from app.services.competencia_ledger import data_iso_no_mes


def _compute_status(parcelas_pagas: int, total_parcelas: int) -> str:
    return "quitado" if parcelas_pagas >= total_parcelas else "ativo"


def preview_parcelamento(
    valor_parcela: float, total_parcelas: int, parcelas_pagas: int
) -> tuple[float, int, float, str]:
    """Resumo para UI: (valor total contrato, parcelas restantes, saldo devedor, status)."""
    tot = max(int(total_parcelas), 0)
    pp = min(max(int(parcelas_pagas), 0), tot)
    restantes = tot - pp
    if tot <= 0:
        return 0.0, restantes, 0.0, "ativo"
    total_contrato = round(float(valor_parcela) * tot, 2)
    sched = schedule_parcel_amounts(total_contrato, tot)
    valor_total = round(sum(sched), 2)
    saldo = round(sum(sched[pp:]), 2) if sched else 0.0
    status = "quitado" if pp >= tot else "ativo"
    return valor_total, restantes, saldo, status


def list_all(conn: Optional[sqlite3.Connection] = None) -> List[Installment]:
    with use(conn) as c:
        rows = installments_repo.list_all_joined(c)
    return [Installment.from_row(r) for r in rows]


def get(
    installment_id: int, conn: Optional[sqlite3.Connection] = None
) -> Optional[Installment]:
    with use(conn) as c:
        row = installments_repo.get_joined(c, installment_id)
    return Installment.from_row(row) if row else None


def create(
    installment: Installment, conn: Optional[sqlite3.Connection] = None
) -> int:
    has_card = installment.cartao_id is not None
    has_acc = installment.account_id is not None
    if has_card == has_acc:
        raise ValueError("Informe cartão ou conta corrente (apenas um)")
    status = _compute_status(installment.parcelas_pagas, installment.total_parcelas)
    with use(conn) as c:
        if has_card:
            row = installments_repo.fetch_card_nome(c, int(installment.cartao_id))
            if not row:
                raise ValueError("Cartão inválido")
            nome_ref = row["nome"]
            pid = installments_repo.insert_on_card(
                c,
                nome_fatura=installment.nome_fatura,
                nome_cartao=nome_ref,
                cartao_id=int(installment.cartao_id),
                mes_referencia=str(installment.mes_referencia),
                valor_parcela=float(installment.valor_parcela),
                total_parcelas=int(installment.total_parcelas),
                parcelas_pagas=int(installment.parcelas_pagas),
                status=status,
                observacao=installment.observacao,
                category_id=installment.category_id,
            )
        else:
            row = installments_repo.fetch_account_nome(c, int(installment.account_id))
            if not row:
                raise ValueError("Conta inválida")
            nome_ref = f"Conta · {row['nome']}"
            pid = installments_repo.insert_on_account(
                c,
                nome_fatura=installment.nome_fatura,
                cartao_label=nome_ref,
                account_id=int(installment.account_id),
                mes_referencia=str(installment.mes_referencia),
                valor_parcela=float(installment.valor_parcela),
                total_parcelas=int(installment.total_parcelas),
                parcelas_pagas=int(installment.parcelas_pagas),
                status=status,
                observacao=installment.observacao,
                category_id=installment.category_id,
            )
    app_events().installments_changed.emit()
    return pid


def update(
    installment: Installment, conn: Optional[sqlite3.Connection] = None
) -> None:
    if installment.id is None:
        raise ValueError("Parcelamento sem id não pode ser atualizado")
    before = get(installment.id, conn=conn)
    if before is None:
        raise ValueError("Parcelamento não encontrado")
    has_card = installment.cartao_id is not None
    has_acc = installment.account_id is not None
    if has_card == has_acc:
        raise ValueError("Informe cartão ou conta corrente (apenas um)")
    status = _compute_status(installment.parcelas_pagas, installment.total_parcelas)
    meio_changed = (before.cartao_id or 0) != (installment.cartao_id or 0) or (
        (before.account_id or 0) != (installment.account_id or 0)
    )
    valor_changed = before.valor_parcela != installment.valor_parcela

    with use(conn) as c:
        if has_card:
            row = installments_repo.fetch_card_nome(c, int(installment.cartao_id))
            if not row:
                raise ValueError("Cartão inválido")
            nome_ref = row["nome"]
            installments_repo.update_on_card(
                c,
                installment_id=int(installment.id),
                nome_fatura=installment.nome_fatura,
                nome_cartao=nome_ref,
                cartao_id=int(installment.cartao_id),
                mes_referencia=str(installment.mes_referencia),
                valor_parcela=float(installment.valor_parcela),
                total_parcelas=int(installment.total_parcelas),
                parcelas_pagas=int(installment.parcelas_pagas),
                status=status,
                observacao=installment.observacao,
                category_id=installment.category_id,
            )
        else:
            row = installments_repo.fetch_account_nome(c, int(installment.account_id))
            if not row:
                raise ValueError("Conta inválida")
            nome_ref = f"Conta · {row['nome']}"
            installments_repo.update_on_account(
                c,
                installment_id=int(installment.id),
                nome_fatura=installment.nome_fatura,
                cartao_label=nome_ref,
                account_id=int(installment.account_id),
                mes_referencia=str(installment.mes_referencia),
                valor_parcela=float(installment.valor_parcela),
                total_parcelas=int(installment.total_parcelas),
                parcelas_pagas=int(installment.parcelas_pagas),
                status=status,
                observacao=installment.observacao,
                category_id=installment.category_id,
            )

        if meio_changed:
            accounts_service.remove_transaction_keys_like_prefix(
                f"installment:{installment.id}:", conn=c
            )

        if installment.account_id and installment.status != "quitado":
            resync = (not meio_changed and valor_changed) or (
                meio_changed
                and before.account_id is not None
                and installment.account_id is not None
            )
            if resync:
                paid_rows = installments_repo.list_paid_ano_meses_for_installment(
                    c, int(installment.id)
                )
                aid = int(installment.account_id)
                vp = float(installment.valor_parcela)
                iid = int(installment.id)
                for pr in paid_rows:
                    ym = str(pr["ano_mes"])
                    data = data_iso_no_mes(ym, 15)
                    accounts_service.upsert_transaction(
                        aid,
                        -vp,
                        data,
                        "parcela",
                        accounts_service.transaction_key_installment(iid, ym),
                        None,
                        conn=c,
                    )
    app_events().installments_changed.emit()


def list_active_ids_for_card_month(
    cartao_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> list[int]:
    from app.models.income_source import installment_month_applies

    with use(conn) as c:
        rows = installments_repo.list_id_mesref_total_ativos_cartao(c, cartao_id)
    out: list[int] = []
    for r in rows:
        if installment_month_applies(
            str(r["mes_referencia"]),
            int(r["total_parcelas"] or 0),
            ano_mes,
        ):
            out.append(int(r["id"]))
    return out


def increment_paid_in_connection(
    conn: sqlite3.Connection, installment_id: int, delta: int = 1
) -> None:
    """Atualiza parcelas_pagas/status na mesma conexão (ex.: dentro de transação maior)."""
    row = installments_repo.fetch_parcelas_pagas_total(conn, installment_id)
    if not row:
        raise ValueError(f"Parcelamento {installment_id} não encontrado")
    tot = int(row["total_parcelas"] or 0)
    pp = int(row["parcelas_pagas"] or 0)
    novo = max(0, min(tot, pp + delta))
    status = _compute_status(novo, tot)
    installments_repo.update_parcelas_pagas_status(conn, installment_id, novo, status)


def increment_paid(
    installment_id: int, delta: int = 1, conn: Optional[sqlite3.Connection] = None
) -> None:
    """Incrementa (ou decrementa) parcelas_pagas respeitando limites."""
    with use(conn) as c:
        increment_paid_in_connection(c, installment_id, delta)
    app_events().installments_changed.emit()


def delete(installment_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        accounts_service.remove_transaction_keys_like_prefix(
            f"installment:{installment_id}:", conn=c
        )
        installments_repo.delete_by_id(c, installment_id)
    app_events().installments_changed.emit()


def total_debt(conn: Optional[sqlite3.Connection] = None) -> float:
    with use(conn) as c:
        return installments_repo.sum_active_debt(c)
