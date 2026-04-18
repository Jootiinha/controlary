"""Operações de CRUD para pagamentos."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from app.database.connection import transaction
from app.models.payment import Payment
from app.services import accounts_service


def list_all() -> List[Payment]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT p.*, a.nome AS conta_nome, c.nome AS cartao_nome, cat.nome AS categoria_nome
              FROM payments p
              LEFT JOIN accounts a ON a.id = p.conta_id
              LEFT JOIN cards c ON c.id = p.cartao_id
              LEFT JOIN categories cat ON cat.id = p.category_id
             ORDER BY date(p.data) DESC, p.id DESC
            """
        ).fetchall()
    return [Payment.from_row(r) for r in rows]


def list_between(data_ini: date, data_fim: date) -> List[Payment]:
    s_ini = data_ini.isoformat()
    s_fim = data_fim.isoformat()
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT p.*, a.nome AS conta_nome, c.nome AS cartao_nome, cat.nome AS categoria_nome
              FROM payments p
              LEFT JOIN accounts a ON a.id = p.conta_id
              LEFT JOIN cards c ON c.id = p.cartao_id
              LEFT JOIN categories cat ON cat.id = p.category_id
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
            SELECT p.*, a.nome AS conta_nome, c.nome AS cartao_nome, cat.nome AS categoria_nome
              FROM payments p
              LEFT JOIN accounts a ON a.id = p.conta_id
              LEFT JOIN cards c ON c.id = p.cartao_id
              LEFT JOIN categories cat ON cat.id = p.category_id
             WHERE p.id = ?
            """,
            (payment_id,),
        ).fetchone()
    return Payment.from_row(row) if row else None


def _validate_origin(payment: Payment) -> None:
    has_acc = payment.conta_id is not None
    has_card = payment.cartao_id is not None
    if has_acc == has_card:
        raise ValueError("Informe conta bancária ou cartão (apenas um)")


def create(payment: Payment, record_ledger: bool = True) -> int:
    """record_ledger=False evita movimentação no livro-caixa (ex.: espelho de fixo já debitado em set_month_status)."""
    _validate_origin(payment)
    conta_txt: Optional[str] = None
    with transaction() as conn:
        if payment.conta_id is not None:
            row = conn.execute(
                "SELECT nome FROM accounts WHERE id = ?", (payment.conta_id,)
            ).fetchone()
            if not row:
                raise ValueError("Conta inválida")
            conta_txt = row["nome"]
            cur = conn.execute(
                """
                INSERT INTO payments (
                    valor, descricao, data, conta, conta_id, cartao_id,
                    forma_pagamento, observacao, category_id
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    payment.valor,
                    payment.descricao,
                    payment.data,
                    conta_txt,
                    payment.conta_id,
                    payment.forma_pagamento,
                    payment.observacao,
                    payment.category_id,
                ),
            )
            pid = int(cur.lastrowid)
            if record_ledger:
                desc = payment.descricao
                if desc and len(desc) > 500:
                    desc = desc[:500]
                accounts_service.upsert_transaction(
                    int(payment.conta_id),
                    -float(payment.valor),
                    payment.data,
                    "pagamento",
                    accounts_service.transaction_key_payment(pid),
                    desc,
                    conn=conn,
                )
            return pid
        row = conn.execute(
            "SELECT nome FROM cards WHERE id = ?", (payment.cartao_id,)
        ).fetchone()
        if not row:
            raise ValueError("Cartão inválido")
        nome_card = row["nome"]
        cur = conn.execute(
            """
            INSERT INTO payments (
                valor, descricao, data, conta, conta_id, cartao_id,
                forma_pagamento, observacao, category_id
            ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?)
            """,
            (
                payment.valor,
                payment.descricao,
                payment.data,
                nome_card,
                payment.cartao_id,
                payment.forma_pagamento,
                payment.observacao,
                payment.category_id,
            ),
        )
        return int(cur.lastrowid)


def update(payment: Payment) -> None:
    if payment.id is None:
        raise ValueError("Pagamento sem id não pode ser atualizado")
    _validate_origin(payment)
    with transaction() as conn:
        accounts_service.remove_transaction_key(
            accounts_service.transaction_key_payment(payment.id), conn=conn
        )
        if payment.conta_id is not None:
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
                       cartao_id = NULL, forma_pagamento = ?, observacao = ?, category_id = ?
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
                    payment.category_id,
                    payment.id,
                ),
            )
            desc = payment.descricao
            if desc and len(desc) > 500:
                desc = desc[:500]
            accounts_service.upsert_transaction(
                int(payment.conta_id),
                -float(payment.valor),
                payment.data,
                "pagamento",
                accounts_service.transaction_key_payment(payment.id),
                desc,
                conn=conn,
            )
            return
        row = conn.execute(
            "SELECT nome FROM cards WHERE id = ?", (payment.cartao_id,)
        ).fetchone()
        if not row:
            raise ValueError("Cartão inválido")
        nome_card = row["nome"]
        conn.execute(
            """
            UPDATE payments
               SET valor = ?, descricao = ?, data = ?, conta = ?, conta_id = NULL,
                   cartao_id = ?, forma_pagamento = ?, observacao = ?, category_id = ?
             WHERE id = ?
            """,
            (
                payment.valor,
                payment.descricao,
                payment.data,
                nome_card,
                payment.cartao_id,
                payment.forma_pagamento,
                payment.observacao,
                payment.category_id,
                payment.id,
            ),
        )


def delete(payment_id: int) -> None:
    with transaction() as conn:
        accounts_service.remove_transaction_key(
            accounts_service.transaction_key_payment(payment_id), conn=conn
        )
        conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
