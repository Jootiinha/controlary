"""Faturas de cartão por competência (agregador mensal)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, List, Optional

from app.database.connection import transaction
from app.models.card_invoice import CardInvoice
from app.services import accounts_service, installments_service


@dataclass(frozen=True)
class ContainedItems:
    parcelas: list[tuple[str, float, int]]
    assinaturas: list[tuple[str, float]]
    pagamentos_cartao: list[tuple[str, float]]


def list_by_month(ano_mes: str) -> List[CardInvoice]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT i.*, c.nome AS cartao_nome
              FROM card_invoices i
              JOIN cards c ON c.id = i.cartao_id
             WHERE i.ano_mes = ?
             ORDER BY c.nome COLLATE NOCASE
            """,
            (ano_mes,),
        ).fetchall()
    return [CardInvoice.from_row(r) for r in rows]


def get_by_id(inv_id: int) -> Optional[CardInvoice]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT i.*, c.nome AS cartao_nome
              FROM card_invoices i
              JOIN cards c ON c.id = i.cartao_id
             WHERE i.id = ?
            """,
            (inv_id,),
        ).fetchone()
    return CardInvoice.from_row(row) if row else None


def get(cartao_id: int, ano_mes: str) -> Optional[CardInvoice]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT i.*, c.nome AS cartao_nome
              FROM card_invoices i
              JOIN cards c ON c.id = i.cartao_id
             WHERE i.cartao_id = ? AND i.ano_mes = ?
            """,
            (cartao_id, ano_mes),
        ).fetchone()
    return CardInvoice.from_row(row) if row else None


def suggested_total_conn(conn: sqlite3.Connection, cartao_id: int, ano_mes: str) -> float:
    r1 = conn.execute(
        """
        SELECT COALESCE(SUM(valor_parcela), 0) AS t
          FROM installments
         WHERE status = 'ativo'
           AND cartao_id = ?
           AND mes_referencia = ?
        """,
        (cartao_id, ano_mes),
    ).fetchone()
    r2 = conn.execute(
        """
        SELECT COALESCE(SUM(valor_mensal), 0) AS t
          FROM subscriptions
         WHERE status = 'ativa'
           AND card_id = ?
        """,
        (cartao_id,),
    ).fetchone()
    r3 = conn.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS t
          FROM payments
         WHERE cartao_id = ?
           AND substr(data, 1, 7) = ?
        """,
        (cartao_id, ano_mes),
    ).fetchone()
    return round(
        float(r1["t"] or 0) + float(r2["t"] or 0) + float(r3["t"] or 0),
        2,
    )


def suggested_total(cartao_id: int, ano_mes: str) -> float:
    with transaction() as conn:
        return suggested_total_conn(conn, cartao_id, ano_mes)


def contained_items(cartao_id: int, ano_mes: str) -> ContainedItems:
    with transaction() as conn:
        par_rows = conn.execute(
            """
            SELECT nome_fatura, valor_parcela, id
              FROM installments
             WHERE status = 'ativo'
               AND cartao_id = ?
               AND mes_referencia = ?
            """,
            (cartao_id, ano_mes),
        ).fetchall()
        sub_rows = conn.execute(
            """
            SELECT nome, valor_mensal
              FROM subscriptions
             WHERE status = 'ativa'
               AND card_id = ?
            """,
            (cartao_id,),
        ).fetchall()
        pay_rows = conn.execute(
            """
            SELECT descricao, valor
              FROM payments
             WHERE cartao_id = ?
               AND substr(data, 1, 7) = ?
            """,
            (cartao_id, ano_mes),
        ).fetchall()
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


def contained_count(cartao_id: int, ano_mes: str) -> int:
    c = contained_items(cartao_id, ano_mes)
    return len(c.parcelas) + len(c.assinaturas) + len(c.pagamentos_cartao)


def upsert_invoice_conn(
    conn: sqlite3.Connection,
    cartao_id: int,
    ano_mes: str,
    valor_total: float,
    status: str = "aberta",
    observacao: Optional[str] = None,
) -> int:
    if status not in ("aberta", "fechada", "paga"):
        raise ValueError("Status de fatura inválido")
    row = conn.execute(
        """
        SELECT id FROM card_invoices
         WHERE cartao_id = ? AND ano_mes = ?
        """,
        (cartao_id, ano_mes),
    ).fetchone()
    if row:
        iid = int(row["id"])
        conn.execute(
            """
            UPDATE card_invoices
               SET valor_total = ?, status = ?, observacao = COALESCE(?, observacao)
             WHERE id = ?
            """,
            (valor_total, status, observacao, iid),
        )
        return iid
    cur = conn.execute(
        """
        INSERT INTO card_invoices (
            cartao_id, ano_mes, valor_total, status, observacao
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (cartao_id, ano_mes, valor_total, status, observacao),
    )
    return int(cur.lastrowid)


def upsert(
    cartao_id: int,
    ano_mes: str,
    valor_total: float,
    status: str = "aberta",
    observacao: Optional[str] = None,
) -> int:
    with transaction() as conn:
        return upsert_invoice_conn(
            conn, cartao_id, ano_mes, valor_total, status, observacao
        )


def mark_paid(
    invoice_id: int,
    conta_pagamento_id: Optional[int],
    pago_em: str,
) -> None:
    with transaction() as conn:
        row = conn.execute(
            "SELECT cartao_id, ano_mes, status FROM card_invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
        if not row:
            raise ValueError("Fatura não encontrada")
        if row["status"] == "paga":
            return
        cartao_id = int(row["cartao_id"])
        ano_mes = row["ano_mes"]
        conn.execute(
            """
            UPDATE card_invoices
               SET status = 'paga', pago_em = ?, conta_pagamento_id = ?
             WHERE id = ?
            """,
            (pago_em, conta_pagamento_id, invoice_id),
        )
        inv_row = conn.execute(
            """
            SELECT valor_total, ano_mes FROM card_invoices WHERE id = ?
            """,
            (invoice_id,),
        ).fetchone()
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
                conn=conn,
            )
    inst_ids = installments_service.list_active_ids_for_card_month(cartao_id, ano_mes)
    for iid in inst_ids:
        installments_service.increment_paid(iid, 1)


def set_status(invoice_id: int, status: str) -> None:
    if status not in ("aberta", "fechada", "paga"):
        raise ValueError("Status inválido")
    with transaction() as conn:
        row = conn.execute(
            "SELECT status FROM card_invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
        if row and row["status"] == "paga" and status != "paga":
            accounts_service.remove_transaction_key(
                accounts_service.transaction_key_invoice(invoice_id), conn=conn
            )
        conn.execute(
            "UPDATE card_invoices SET status = ? WHERE id = ?",
            (status, invoice_id),
        )


def ensure_row_for_card_month(cartao_id: int, ano_mes: str) -> CardInvoice:
    """Garante linha de fatura; valor inicial = sugerido."""
    existing = get(cartao_id, ano_mes)
    if existing:
        return existing
    sug = suggested_total(cartao_id, ano_mes)
    iid = upsert(cartao_id, ano_mes, sug, "aberta")
    inv = get_by_id(iid)
    if inv is None:
        raise RuntimeError("Falha ao criar fatura")
    return inv


def list_all_cards_with_invoice_hint(ano_mes: str) -> list[dict[str, Any]]:
    """Todos os cartões com totais sugeridos e linha de fatura se existir."""
    from app.services import cards_service

    out: list[dict[str, Any]] = []
    for card in cards_service.list_all():
        if card.id is None:
            continue
        cid = card.id
        sug = suggested_total(cid, ano_mes)
        inv = get(cid, ano_mes)
        cnt = contained_count(cid, ano_mes)
        out.append(
            {
                "card": card,
                "suggested": sug,
                "invoice": inv,
                "contained_count": cnt,
            }
        )
    return out
