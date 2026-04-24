"""SQL puro para subscriptions."""
from __future__ import annotations

import sqlite3
from typing import Optional


def list_all_joined(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT s.*,
               COALESCE(a.nome, c.nome, s.conta_cartao) AS meio_label,
               cat.nome AS categoria_nome
          FROM subscriptions s
          LEFT JOIN accounts a ON a.id = s.account_id
          LEFT JOIN cards c ON c.id = s.card_id
          LEFT JOIN categories cat ON cat.id = s.category_id
         ORDER BY CASE s.status
                    WHEN 'ativa' THEN 0
                    WHEN 'pausada' THEN 1
                    ELSE 2
                  END,
                  s.nome COLLATE NOCASE
        """
    ).fetchall()


def get_joined(conn: sqlite3.Connection, sub_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT s.*,
               COALESCE(a.nome, c.nome, s.conta_cartao) AS meio_label,
               cat.nome AS categoria_nome
          FROM subscriptions s
          LEFT JOIN accounts a ON a.id = s.account_id
          LEFT JOIN cards c ON c.id = s.card_id
          LEFT JOIN categories cat ON cat.id = s.category_id
         WHERE s.id = ?
        """,
        (sub_id,),
    ).fetchone()


def fetch_category_nome(
    conn: sqlite3.Connection, category_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT nome FROM categories WHERE id = ?",
        (category_id,),
    ).fetchone()


def fetch_account_nome(conn: sqlite3.Connection, account_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT nome FROM accounts WHERE id = ?",
        (account_id,),
    ).fetchone()


def fetch_card_nome(conn: sqlite3.Connection, card_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT nome FROM cards WHERE id = ?",
        (card_id,),
    ).fetchone()


def insert_subscription(
    conn: sqlite3.Connection,
    *,
    nome: str,
    categoria: Optional[str],
    valor_mensal: float,
    dia_cobranca: int,
    forma_pagamento: str,
    conta_cartao: Optional[str],
    account_id: Optional[int],
    card_id: Optional[int],
    status: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO subscriptions (
            nome, categoria, valor_mensal, dia_cobranca,
            forma_pagamento, conta_cartao, account_id, card_id, status, observacao,
            category_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            categoria,
            valor_mensal,
            dia_cobranca,
            forma_pagamento,
            conta_cartao,
            account_id,
            card_id,
            status,
            observacao,
            category_id,
        ),
    )
    return int(cur.lastrowid)


def update_subscription(
    conn: sqlite3.Connection,
    *,
    sub_id: int,
    nome: str,
    categoria: Optional[str],
    valor_mensal: float,
    dia_cobranca: int,
    forma_pagamento: str,
    conta_cartao: Optional[str],
    account_id: Optional[int],
    card_id: Optional[int],
    status: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> None:
    conn.execute(
        """
        UPDATE subscriptions
           SET nome = ?, categoria = ?, valor_mensal = ?, dia_cobranca = ?,
               forma_pagamento = ?, conta_cartao = ?, account_id = ?, card_id = ?,
               status = ?, observacao = ?, category_id = ?
         WHERE id = ?
        """,
        (
            nome,
            categoria,
            valor_mensal,
            dia_cobranca,
            forma_pagamento,
            conta_cartao,
            account_id,
            card_id,
            status,
            observacao,
            category_id,
            sub_id,
        ),
    )


def list_paid_ano_meses(conn: sqlite3.Connection, subscription_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ano_mes FROM subscription_months
         WHERE subscription_id = ? AND status = 'pago'
        """,
        (subscription_id,),
    ).fetchall()


def delete_by_id(conn: sqlite3.Connection, sub_id: int) -> None:
    conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))


def row_total_active(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute(
        """
        SELECT COUNT(*) AS qtd, COALESCE(SUM(valor_mensal), 0) AS total
          FROM subscriptions
         WHERE status = 'ativa'
        """
    ).fetchone()


def sum_active_not_on_card(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor_mensal), 0) AS total
          FROM subscriptions
         WHERE status = 'ativa'
           AND card_id IS NULL
        """
    ).fetchone()
    return float(row["total"] or 0)
