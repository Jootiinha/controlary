"""Operações de CRUD para pagamentos."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from app.database.connection import transaction
from app.models.payment import Payment


def list_all() -> List[Payment]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT p.*, a.nome AS conta_nome
              FROM payments p
              LEFT JOIN accounts a ON a.id = p.conta_id
             ORDER BY date(p.data) DESC, p.id DESC
            """
        ).fetchall()
    return [Payment.from_row(r) for r in rows]


def list_between(data_ini: date, data_fim: date) -> List[Payment]:
    """Pagamentos com `data` no intervalo inclusivo (por dia civil)."""
    s_ini = data_ini.isoformat()
    s_fim = data_fim.isoformat()
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT p.*, a.nome AS conta_nome
              FROM payments p
              LEFT JOIN accounts a ON a.id = p.conta_id
             WHERE date(p.data) BETWEEN date(?) AND date(?)
             ORDER BY date(p.data), p.id
            """,
            (s_ini, s_fim),
        ).fetchall()
    return [Payment.from_row(r) for r in rows]


def get(payment_id: int) -> Optional[Payment]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT p.*, a.nome AS conta_nome
              FROM payments p
              LEFT JOIN accounts a ON a.id = p.conta_id
             WHERE p.id = ?
            """,
            (payment_id,),
        ).fetchone()
    return Payment.from_row(row) if row else None


def create(payment: Payment) -> int:
    if not payment.conta_id:
        raise ValueError("Selecione uma conta")
    nome_conta = None
    with transaction() as conn:
        row = conn.execute(
            "SELECT nome FROM accounts WHERE id = ?", (payment.conta_id,)
        ).fetchone()
        if not row:
            raise ValueError("Conta inválida")
        nome_conta = row["nome"]
        cur = conn.execute(
            """
            INSERT INTO payments (valor, descricao, data, conta, conta_id, forma_pagamento, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payment.valor,
                payment.descricao,
                payment.data,
                nome_conta,
                payment.conta_id,
                payment.forma_pagamento,
                payment.observacao,
            ),
        )
        return int(cur.lastrowid)


def update(payment: Payment) -> None:
    if payment.id is None:
        raise ValueError("Pagamento sem id não pode ser atualizado")
    if not payment.conta_id:
        raise ValueError("Selecione uma conta")
    with transaction() as conn:
        row = conn.execute(
            "SELECT nome FROM accounts WHERE id = ?", (payment.conta_id,)
        ).fetchone()
        if not row:
            raise ValueError("Conta inválida")
        nome_conta = row["nome"]
        conn.execute(
            """
            UPDATE payments
               SET valor = ?, descricao = ?, data = ?, conta = ?, conta_id = ?,
                   forma_pagamento = ?, observacao = ?
             WHERE id = ?
            """,
            (
                payment.valor,
                payment.descricao,
                payment.data,
                nome_conta,
                payment.conta_id,
                payment.forma_pagamento,
                payment.observacao,
                payment.id,
            ),
        )


def delete(payment_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
