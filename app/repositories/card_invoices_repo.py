"""SQL puro para card_invoices e leituras auxiliares (parcelas, assinaturas, pagamentos no cartão)."""
from __future__ import annotations

import sqlite3
from typing import Optional


def list_by_month(conn: sqlite3.Connection, ano_mes: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, c.nome AS cartao_nome
          FROM card_invoices i
          JOIN cards c ON c.id = i.cartao_id
         WHERE i.ano_mes = ?
         ORDER BY c.nome COLLATE NOCASE
        """,
        (ano_mes,),
    ).fetchall()


def get_row_by_id(conn: sqlite3.Connection, inv_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, c.nome AS cartao_nome
          FROM card_invoices i
          JOIN cards c ON c.id = i.cartao_id
         WHERE i.id = ?
        """,
        (inv_id,),
    ).fetchone()


def get_row_by_card_month(
    conn: sqlite3.Connection, cartao_id: int, ano_mes: str
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, c.nome AS cartao_nome
          FROM card_invoices i
          JOIN cards c ON c.id = i.cartao_id
         WHERE i.cartao_id = ? AND i.ano_mes = ?
        """,
        (cartao_id, ano_mes),
    ).fetchone()


def list_installment_parcel_refs_ativos_por_cartao(
    conn: sqlite3.Connection, cartao_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT valor_parcela, mes_referencia, total_parcelas
          FROM installments
         WHERE status = 'ativo'
           AND cartao_id = ?
        """,
        (cartao_id,),
    ).fetchall()


def list_installment_contained_rows(
    conn: sqlite3.Connection, cartao_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT nome_fatura, valor_parcela, id, mes_referencia, total_parcelas
          FROM installments
         WHERE status = 'ativo'
           AND cartao_id = ?
        """,
        (cartao_id,),
    ).fetchall()


def sum_subscriptions_valor_mensal_ativas_cartao(
    conn: sqlite3.Connection, cartao_id: int
) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor_mensal), 0) AS t
          FROM subscriptions
         WHERE status = 'ativa'
           AND card_id = ?
        """,
        (cartao_id,),
    ).fetchone()
    return float(row["t"] or 0)


def sum_payments_cartao_mes(
    conn: sqlite3.Connection, cartao_id: int, ano_mes: str
) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS t
          FROM payments
         WHERE cartao_id = ?
           AND substr(data, 1, 7) = ?
        """,
        (cartao_id, ano_mes),
    ).fetchone()
    return float(row["t"] or 0)


def list_subscriptions_nome_valor_ativas_cartao(
    conn: sqlite3.Connection, cartao_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT nome, valor_mensal
          FROM subscriptions
         WHERE status = 'ativa'
           AND card_id = ?
        """,
        (cartao_id,),
    ).fetchall()


def list_payments_cartao_mes(
    conn: sqlite3.Connection, cartao_id: int, ano_mes: str
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT descricao, valor
          FROM payments
         WHERE cartao_id = ?
           AND substr(data, 1, 7) = ?
        """,
        (cartao_id, ano_mes),
    ).fetchall()


def find_invoice_id_by_card_month(
    conn: sqlite3.Connection, cartao_id: int, ano_mes: str
) -> Optional[int]:
    row = conn.execute(
        """
        SELECT id FROM card_invoices
         WHERE cartao_id = ? AND ano_mes = ?
        """,
        (cartao_id, ano_mes),
    ).fetchone()
    return int(row["id"]) if row else None


def fetch_invoice_status_by_id(
    conn: sqlite3.Connection, inv_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT status FROM card_invoices WHERE id = ?",
        (inv_id,),
    ).fetchone()


def update_invoice_valor_status_obs(
    conn: sqlite3.Connection,
    inv_id: int,
    valor_total: float,
    status: str,
    observacao: Optional[str],
) -> None:
    conn.execute(
        """
        UPDATE card_invoices
           SET valor_total = ?, status = ?, observacao = COALESCE(?, observacao)
         WHERE id = ?
        """,
        (valor_total, status, observacao, inv_id),
    )


def insert_invoice(
    conn: sqlite3.Connection,
    cartao_id: int,
    ano_mes: str,
    valor_total: float,
    status: str,
    observacao: Optional[str],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO card_invoices (
            cartao_id, ano_mes, valor_total, status, observacao
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (cartao_id, ano_mes, valor_total, status, observacao),
    )
    return int(cur.lastrowid)


def fetch_invoice_mark_paid_header(
    conn: sqlite3.Connection, invoice_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT cartao_id, ano_mes, status, COALESCE(valor_total, 0) AS valor_total,
               COALESCE(historico, 0) AS historico
          FROM card_invoices WHERE id = ?
        """,
        (invoice_id,),
    ).fetchone()


def update_invoice_paid(
    conn: sqlite3.Connection,
    invoice_id: int,
    pago_em: str,
    conta_pagamento_id: Optional[int],
    historico: int = 0,
) -> None:
    conn.execute(
        """
        UPDATE card_invoices
           SET status = 'paga', pago_em = ?, conta_pagamento_id = ?,
               historico = ?
         WHERE id = ?
        """,
        (pago_em, conta_pagamento_id, historico, invoice_id),
    )


def fetch_valor_total_ano_mes(
    conn: sqlite3.Connection, invoice_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT valor_total, ano_mes FROM card_invoices WHERE id = ?
        """,
        (invoice_id,),
    ).fetchone()


def fetch_invoice_status_cartao_ano(
    conn: sqlite3.Connection, invoice_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT status, cartao_id, ano_mes, COALESCE(historico, 0) AS historico
          FROM card_invoices WHERE id = ?
        """,
        (invoice_id,),
    ).fetchone()


def update_invoice_status_only(
    conn: sqlite3.Connection, invoice_id: int, status: str
) -> None:
    conn.execute(
        """
        UPDATE card_invoices
           SET status = ?,
               historico = CASE
                   WHEN ? IN ('aberta', 'fechada') THEN 0
                   ELSE historico
               END
         WHERE id = ?
        """,
        (status, status, invoice_id),
    )


def history_invoice_rows(
    conn: sqlite3.Connection, start_ym: str, end_ym: str
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT cartao_id, ano_mes, valor_total
          FROM card_invoices
         WHERE ano_mes BETWEEN ? AND ?
           AND status IN ('fechada', 'paga')
           AND valor_total > 0
         ORDER BY cartao_id, ano_mes
        """,
        (start_ym, end_ym),
    ).fetchall()
