"""Agregações de totais de despesa por mês civil."""
from __future__ import annotations

import sqlite3
from typing import Optional


def sum_account_debits_excl_fatura(conn: sqlite3.Connection, ano_mes: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS t
          FROM account_transactions
         WHERE substr(data, 1, 7) = ?
           AND valor < 0
           AND COALESCE(origem, '') != 'fatura'
        """,
        (ano_mes,),
    ).fetchone()
    return abs(float(row["t"] or 0))


def sum_card_payments_month(conn: sqlite3.Connection, ano_mes: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS t
          FROM payments
         WHERE cartao_id IS NOT NULL
           AND substr(data, 1, 7) = ?
        """,
        (ano_mes,),
    ).fetchone()
    return float(row["t"] or 0)


def sum_received_income_months(conn: sqlite3.Connection, ano_mes: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(COALESCE(im.valor_efetivo, i.valor_mensal)), 0) AS t
          FROM income_months im
          JOIN income_sources i ON i.id = im.income_source_id
         WHERE im.ano_mes = ?
           AND im.status = 'recebido'
           AND i.ativo = 1
        """,
        (ano_mes,),
    ).fetchone()
    return round(float(row["t"] or 0), 2)
