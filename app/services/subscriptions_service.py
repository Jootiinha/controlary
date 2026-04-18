"""Operações de CRUD para assinaturas recorrentes."""
from __future__ import annotations

from typing import List, Optional

from app.database.connection import transaction
from app.models.subscription import Subscription
from app.services import accounts_service


def list_all() -> List[Subscription]:
    with transaction() as conn:
        rows = conn.execute(
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
    return [Subscription.from_row(r) for r in rows]


def get(sub_id: int) -> Optional[Subscription]:
    with transaction() as conn:
        row = conn.execute(
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
    return Subscription.from_row(row) if row else None


def _legacy_categoria(conn, sub: Subscription) -> Optional[str]:
    if sub.category_id is None:
        return sub.categoria
    r = conn.execute(
        "SELECT nome FROM categories WHERE id = ?", (sub.category_id,)
    ).fetchone()
    return r["nome"] if r else sub.categoria


def create(sub: Subscription) -> int:
    with transaction() as conn:
        label = _meio_label(conn, sub.account_id, sub.card_id)
        cat_txt = _legacy_categoria(conn, sub)
        cur = conn.execute(
            """
            INSERT INTO subscriptions (
                nome, categoria, valor_mensal, dia_cobranca,
                forma_pagamento, conta_cartao, account_id, card_id, status, observacao,
                category_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sub.nome,
                cat_txt,
                sub.valor_mensal,
                sub.dia_cobranca,
                sub.forma_pagamento,
                label,
                sub.account_id,
                sub.card_id,
                sub.status,
                sub.observacao,
                sub.category_id,
            ),
        )
        return int(cur.lastrowid)


def update(sub: Subscription) -> None:
    if sub.id is None:
        raise ValueError("Assinatura sem id não pode ser atualizada")
    with transaction() as conn:
        label = _meio_label(conn, sub.account_id, sub.card_id)
        cat_txt = _legacy_categoria(conn, sub)
        conn.execute(
            """
            UPDATE subscriptions
               SET nome = ?, categoria = ?, valor_mensal = ?, dia_cobranca = ?,
                   forma_pagamento = ?, conta_cartao = ?, account_id = ?, card_id = ?,
                   status = ?, observacao = ?, category_id = ?
             WHERE id = ?
            """,
            (
                sub.nome,
                cat_txt,
                sub.valor_mensal,
                sub.dia_cobranca,
                sub.forma_pagamento,
                label,
                sub.account_id,
                sub.card_id,
                sub.status,
                sub.observacao,
                sub.category_id,
                sub.id,
            ),
        )


def _meio_label(conn, account_id: Optional[int], card_id: Optional[int]) -> Optional[str]:
    if account_id:
        r = conn.execute("SELECT nome FROM accounts WHERE id = ?", (account_id,)).fetchone()
        return r["nome"] if r else None
    if card_id:
        r = conn.execute("SELECT nome FROM cards WHERE id = ?", (card_id,)).fetchone()
        return r["nome"] if r else None
    return None


def delete(sub_id: int) -> None:
    with transaction() as conn:
        accounts_service.remove_transaction_keys_like_prefix(
            f"subscription:{sub_id}:", conn=conn
        )
        conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))


def total_active() -> tuple[int, float]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS qtd, COALESCE(SUM(valor_mensal), 0) AS total
              FROM subscriptions
             WHERE status = 'ativa'
            """
        ).fetchone()
    return int(row["qtd"] or 0), float(row["total"] or 0)


def sum_active_not_on_card() -> float:
    """Soma assinaturas ativas pagas em conta (sem cartão)."""
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_mensal), 0) AS total
              FROM subscriptions
             WHERE status = 'ativa'
               AND card_id IS NULL
            """
        ).fetchone()
    return float(row["total"] or 0)
