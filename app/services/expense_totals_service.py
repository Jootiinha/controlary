"""Totais de despesa por mês civil (alinhado ao livro-caixa + cartão)."""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.database.connection import use
from app.repositories import expense_totals_repo


def total_despesa_mes(ano_mes: str, conn: Optional[sqlite3.Connection] = None) -> float:
    """Despesa no mês YYYY-MM: saídas reais em todas as contas (livro-caixa)
    mais compras no cartão com data nesse mês."""
    with use(conn) as c:
        caixa = expense_totals_repo.sum_account_debits_excl_fatura(c, ano_mes)
        cartao = expense_totals_repo.sum_card_payments_month(c, ano_mes)
    return round(caixa + cartao, 2)
