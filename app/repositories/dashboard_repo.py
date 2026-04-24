"""Agregações SQL usadas pelo dashboard."""
from __future__ import annotations

import sqlite3


def sum_payments_conta_in_month(conn: sqlite3.Connection, ano_mes: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(p.valor), 0) AS t
          FROM payments p
         WHERE substr(p.data, 1, 7) = ?
           AND p.cartao_id IS NULL
           AND p.conta_id IS NOT NULL
        """,
        (ano_mes,),
    ).fetchone()
    return float(row["t"] or 0)


def sum_subscriptions_conta_pending_month(
    conn: sqlite3.Connection, ano_mes: str
) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(s.valor_mensal), 0) AS t
          FROM subscriptions s
         WHERE s.status = 'ativa'
           AND s.card_id IS NULL
           AND s.account_id IS NOT NULL
           AND NOT EXISTS (
               SELECT 1 FROM subscription_months sm
                WHERE sm.subscription_id = s.id
                  AND sm.ano_mes = ?
                  AND sm.status = 'pago'
           )
        """,
        (ano_mes,),
    ).fetchone()
    return float(row["t"] or 0)


def sum_payments_conta_month_without_ledger_mirror(
    conn: sqlite3.Connection, ano_mes: str
) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(p.valor), 0) AS total
          FROM payments p
         WHERE substr(p.data, 1, 7) = ?
           AND p.cartao_id IS NULL
           AND p.conta_id IS NOT NULL
           AND NOT EXISTS (
               SELECT 1 FROM account_transactions t
                WHERE t.transaction_key = ('payment:' || p.id)
           )
        """,
        (ano_mes,),
    ).fetchone()
    return float(row["total"] or 0)


def count_subscriptions_ativas_conta(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS qtd
          FROM subscriptions
         WHERE status = 'ativa'
           AND card_id IS NULL
        """
    ).fetchone()
    return int(row["qtd"] or 0)


def row_subscriptions_kpi(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute(
        """
        SELECT COUNT(*) AS qtd,
               COALESCE(SUM(valor_mensal), 0) AS total,
               COALESCE(SUM(CASE WHEN card_id IS NULL THEN 1 ELSE 0 END), 0) AS em_conta,
               COALESCE(SUM(CASE WHEN card_id IS NOT NULL THEN 1 ELSE 0 END), 0) AS no_cartao
          FROM subscriptions
         WHERE status = 'ativa'
        """
    ).fetchone()


def count_installments_ativos(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS qtd FROM installments WHERE status = 'ativo'"
    ).fetchone()
    return int(row["qtd"] or 0)


def sum_saldo_devedor_parcelas(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor_parcela * (total_parcelas - parcelas_pagas)), 0) AS saldo
          FROM installments WHERE status = 'ativo'
        """
    ).fetchone()
    return float(row["saldo"] or 0)


def list_card_ids(conn: sqlite3.Connection) -> list[int]:
    return [int(r["id"]) for r in conn.execute("SELECT id FROM cards").fetchall()]


def fetch_invoice_valor_status(
    conn: sqlite3.Connection, cartao_id: int, ano_mes: str
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT COALESCE(valor_total, 0) AS vt, status
          FROM card_invoices
         WHERE cartao_id = ? AND ano_mes = ?
        """,
        (cartao_id, ano_mes),
    ).fetchone()


def gastos_por_conta_rows(conn: sqlite3.Connection, mes: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT CASE
                 WHEN p.cartao_id IS NOT NULL THEN 'Cartão · ' || COALESCE(c.nome, '?')
                 ELSE COALESCE(a.nome, p.conta, '(sem conta)')
               END AS nome_origem,
               COALESCE(SUM(p.valor), 0) AS total
          FROM payments p
          LEFT JOIN accounts a ON a.id = p.conta_id
          LEFT JOIN cards c ON c.id = p.cartao_id
         WHERE substr(p.data, 1, 7) = ?
         GROUP BY nome_origem
         ORDER BY total DESC
        """,
        (mes,),
    ).fetchall()


def gastos_por_forma_rows(conn: sqlite3.Connection, mes: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT forma_pagamento, COALESCE(SUM(valor), 0) AS total
          FROM payments
         WHERE substr(data, 1, 7) = ?
         GROUP BY forma_pagamento
         ORDER BY total DESC
        """,
        (mes,),
    ).fetchall()
