"""Faturas de cartão por competência (agregador mensal)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, List, Optional

from app.database.connection import use
from app.events import app_events
from app.models.card_invoice import CardInvoice
from app.models.income_source import installment_month_applies
from app.repositories import card_invoices_repo, installments_repo
from app.services import accounts_service, installments_service


@dataclass(frozen=True)
class ContainedItems:
    parcelas: list[tuple[str, float, int]]
    assinaturas: list[tuple[str, float]]
    pagamentos_cartao: list[tuple[str, float]]


def list_by_month(
    ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> List[CardInvoice]:
    with use(conn) as c:
        rows = card_invoices_repo.list_by_month(c, ano_mes)
    return [CardInvoice.from_row(r) for r in rows]


def get_by_id(
    inv_id: int, conn: Optional[sqlite3.Connection] = None
) -> Optional[CardInvoice]:
    with use(conn) as c:
        row = card_invoices_repo.get_row_by_id(c, inv_id)
    return CardInvoice.from_row(row) if row else None


def get(
    cartao_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[CardInvoice]:
    with use(conn) as c:
        row = card_invoices_repo.get_row_by_card_month(c, cartao_id, ano_mes)
    return CardInvoice.from_row(row) if row else None


def _sum_parcelas_cartao_no_mes(
    c: sqlite3.Connection, cartao_id: int, ano_mes: str
) -> float:
    rows = card_invoices_repo.list_installment_parcel_refs_ativos_por_cartao(
        c, cartao_id
    )
    total = 0.0
    for r in rows:
        if installment_month_applies(
            str(r["mes_referencia"]),
            int(r["total_parcelas"] or 0),
            ano_mes,
        ):
            total += float(r["valor_parcela"] or 0)
    return total


def suggested_total(
    cartao_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> float:
    with use(conn) as c:
        parcelas = _sum_parcelas_cartao_no_mes(c, cartao_id, ano_mes)
        sub_sum = card_invoices_repo.sum_subscriptions_valor_mensal_ativas_cartao(
            c, cartao_id
        )
        pay_sum = card_invoices_repo.sum_payments_cartao_mes(c, cartao_id, ano_mes)
    return round(parcelas + sub_sum + pay_sum, 2)


def contained_items(
    cartao_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> ContainedItems:
    with use(conn) as c:
        all_par = card_invoices_repo.list_installment_contained_rows(c, cartao_id)
        par_rows = [
            r
            for r in all_par
            if installment_month_applies(
                str(r["mes_referencia"]),
                int(r["total_parcelas"] or 0),
                ano_mes,
            )
        ]
        sub_rows = card_invoices_repo.list_subscriptions_nome_valor_ativas_cartao(
            c, cartao_id
        )
        pay_rows = card_invoices_repo.list_payments_cartao_mes(c, cartao_id, ano_mes)
    parcelas = [
        (r["nome_fatura"], float(r["valor_parcela"]), int(r["id"]))
        for r in par_rows
    ]
    assinaturas = [(r["nome"], float(r["valor_mensal"])) for r in sub_rows]
    pagamentos = [(r["descricao"], float(r["valor"])) for r in pay_rows]
    return ContainedItems(
        parcelas=parcelas,
        assinaturas=assinaturas,
        pagamentos_cartao=pagamentos,
    )


def contained_count(
    cartao_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> int:
    ci = contained_items(cartao_id, ano_mes, conn=conn)
    return len(ci.parcelas) + len(ci.assinaturas) + len(ci.pagamentos_cartao)


def upsert(
    cartao_id: int,
    ano_mes: str,
    valor_total: float,
    status: str = "aberta",
    observacao: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    if status not in ("aberta", "fechada", "paga"):
        raise ValueError("Status de fatura inválido")
    with use(conn) as c:
        iid = card_invoices_repo.find_invoice_id_by_card_month(c, cartao_id, ano_mes)
        if iid is not None:
            prev = card_invoices_repo.fetch_invoice_status_by_id(c, iid)
            if (
                prev
                and prev["status"] == "paga"
                and status != "paga"
            ):
                raise ValueError(
                    "Fatura já está paga. Reabra a fatura antes de salvar como rascunho ou fechada."
                )
            card_invoices_repo.update_invoice_valor_status_obs(
                c, iid, valor_total, status, observacao
            )
            out_id = iid
        else:
            out_id = card_invoices_repo.insert_invoice(
                c, cartao_id, ano_mes, valor_total, status, observacao
            )
    app_events().card_invoices_changed.emit()
    return out_id


def mark_paid(
    invoice_id: int,
    conta_pagamento_id: Optional[int],
    pago_em: str,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    with use(conn) as c:
        row = card_invoices_repo.fetch_invoice_mark_paid_header(c, invoice_id)
        if not row:
            raise ValueError("Fatura não encontrada")
        if row["status"] == "paga":
            return
        if float(row["valor_total"] or 0) > 0 and conta_pagamento_id is None:
            raise ValueError(
                "Informe a conta utilizada para débito no livro-caixa ao pagar a fatura."
            )
        cartao_id = int(row["cartao_id"])
        ano_mes = row["ano_mes"]
        card_invoices_repo.update_invoice_paid(
            c, invoice_id, pago_em, conta_pagamento_id, historico=0
        )
        inv_row = card_invoices_repo.fetch_valor_total_ano_mes(c, invoice_id)
        if (
            conta_pagamento_id is not None
            and inv_row
            and float(inv_row["valor_total"] or 0) > 0
        ):
            accounts_service.upsert_transaction(
                int(conta_pagamento_id),
                -float(inv_row["valor_total"]),
                pago_em,
                "fatura",
                accounts_service.transaction_key_invoice(invoice_id),
                f"Fatura {inv_row['ano_mes']}",
                conn=c,
            )
        for r in installments_repo.list_id_mesref_total_ativos_cartao(c, cartao_id):
            if not installment_month_applies(
                str(r["mes_referencia"]),
                int(r["total_parcelas"] or 0),
                ano_mes,
            ):
                continue
            installments_service.increment_paid_in_connection(c, int(r["id"]), 1)
    app_events().card_invoices_changed.emit()


def mark_paid_historico(
    invoice_id: int, pago_em: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    with use(conn) as c:
        row = card_invoices_repo.fetch_invoice_mark_paid_header(c, invoice_id)
        if not row or row["status"] == "paga":
            return
        card_invoices_repo.update_invoice_paid(
            c, invoice_id, pago_em, None, historico=1
        )
    app_events().card_invoices_changed.emit()


def set_status(
    invoice_id: int, status: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    if status not in ("aberta", "fechada", "paga"):
        raise ValueError("Status inválido")
    with use(conn) as c:
        row = card_invoices_repo.fetch_invoice_status_cartao_ano(c, invoice_id)
        if row and row["status"] == "paga" and status != "paga":
            is_hist = bool(int(row["historico"] or 0))
            if not is_hist:
                accounts_service.remove_transaction_key(
                    accounts_service.transaction_key_invoice(invoice_id), conn=c
                )
                cartao_id = int(row["cartao_id"])
                ano_mes = str(row["ano_mes"])
                for r in installments_repo.list_id_mesref_total_cartao_ativo_quitado(
                    c, cartao_id
                ):
                    if not installment_month_applies(
                        str(r["mes_referencia"]),
                        int(r["total_parcelas"] or 0),
                        ano_mes,
                    ):
                        continue
                    installments_service.increment_paid_in_connection(
                        c, int(r["id"]), -1
                    )
        card_invoices_repo.update_invoice_status_only(c, invoice_id, status)
    app_events().card_invoices_changed.emit()


def ensure_row_for_card_month(
    cartao_id: int, ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> CardInvoice:
    """Garante linha de fatura; valor inicial = sugerido."""
    existing = get(cartao_id, ano_mes, conn=conn)
    if existing:
        return existing
    sug = suggested_total(cartao_id, ano_mes, conn=conn)
    iid = upsert(cartao_id, ano_mes, sug, "aberta", conn=conn)
    inv = get_by_id(iid, conn=conn)
    if inv is None:
        raise RuntimeError("Falha ao criar fatura")
    return inv


def list_all_cards_with_invoice_hint(
    ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> list[dict[str, Any]]:
    """Todos os cartões com totais sugeridos e linha de fatura se existir."""
    from app.services import cards_service

    out: list[dict[str, Any]] = []
    for card in cards_service.list_all(conn=conn):
        if card.id is None:
            continue
        cid = card.id
        sug = suggested_total(cid, ano_mes, conn=conn)
        inv = get(cid, ano_mes, conn=conn)
        cnt = contained_count(cid, ano_mes, conn=conn)
        out.append(
            {
                "card": card,
                "suggested": sug,
                "invoice": inv,
                "contained_count": cnt,
            }
        )
    return out


def history_by_card(
    start_ym: str,
    end_ym: str,
    conn: Optional[sqlite3.Connection] = None,
) -> dict[int, list[tuple[str, float]]]:
    """Por cartão, lista de (ano_mes, valor_total) no intervalo [start_ym, end_ym].

    Só faturas com status ``fechada`` ou ``paga`` e ``valor_total > 0``.
    Cada lista está ordenada por ``ano_mes`` ascendente.
    """
    with use(conn) as c:
        rows = card_invoices_repo.history_invoice_rows(c, start_ym, end_ym)
    out: dict[int, list[tuple[str, float]]] = {}
    for r in rows:
        cid = int(r["cartao_id"])
        ym = str(r["ano_mes"])
        v = float(r["valor_total"] or 0.0)
        out.setdefault(cid, []).append((ym, round(v, 2)))
    return out
