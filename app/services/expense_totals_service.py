"""Totais de despesa por mês civil (alinhado ao livro-caixa + cartão)."""
from __future__ import annotations

from app.database.connection import transaction


def total_despesa_mes(ano_mes: str) -> float:
    """Despesa no mês YYYY-MM: saídas reais em todas as contas (livro-caixa)
    mais compras no cartão com data nesse mês.

    O livro-caixa inclui pagamentos em débito/conta, fixos marcados como pagos,
    etc. Débitos ``origem = 'fatura'`` são excluídos daqui para evitar dupla
    contagem com ``payments`` no cartão no mesmo mês civil. Compras no cartão
    entram em ``payments`` e normalmente só debitam a conta no pagamento da
    fatura (outro mês). Transferências ou ajustes manuais contam como saída.
    """
    with transaction() as conn:
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
    caixa = abs(float(row["t"] or 0))
    with transaction() as conn:
        row2 = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS t
              FROM payments
             WHERE cartao_id IS NOT NULL
               AND substr(data, 1, 7) = ?
            """,
            (ano_mes,),
        ).fetchone()
    cartao = float(row2["t"] or 0)
    return round(caixa + cartao, 2)
