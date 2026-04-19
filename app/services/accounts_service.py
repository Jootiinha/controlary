"""CRUD de contas bancárias e livro-caixa (account_transactions)."""
from __future__ import annotations

import sqlite3
import uuid
from typing import List, Optional

from app.database.connection import transaction
from app.models.account import Account


def upsert_transaction(
    account_id: int,
    valor: float,
    data: str,
    origem: str,
    transaction_key: str,
    descricao: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Insere ou substitui movimentação com a mesma transaction_key (idempotente)."""

    def _run(c: sqlite3.Connection) -> int:
        row = c.execute(
            "SELECT id FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if not row:
            raise ValueError("Conta inválida")
        c.execute(
            "DELETE FROM account_transactions WHERE transaction_key = ?",
            (transaction_key,),
        )
        cur = c.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (account_id, data, valor, origem, transaction_key, descricao),
        )
        return int(cur.lastrowid)

    if conn is not None:
        return _run(conn)
    with transaction() as c:
        return _run(c)


def remove_transaction_key(
    transaction_key: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    def _run(c: sqlite3.Connection) -> None:
        c.execute(
            "DELETE FROM account_transactions WHERE transaction_key = ?",
            (transaction_key,),
        )

    if conn is not None:
        _run(conn)
    else:
        with transaction() as c:
            _run(c)


def remove_transaction_keys_like_prefix(
    prefix: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    """Remove movimentações cujo transaction_key começa com prefix (ex.: 'fixed:3:')."""

    def _run(c: sqlite3.Connection) -> None:
        c.execute(
            "DELETE FROM account_transactions WHERE transaction_key LIKE ?",
            (prefix + "%",),
        )

    if conn is not None:
        _run(conn)
    else:
        with transaction() as c:
            _run(c)


def transaction_key_payment(payment_id: int) -> str:
    return f"payment:{payment_id}"


def transaction_key_invoice(invoice_id: int) -> str:
    return f"invoice:{invoice_id}"


def transaction_key_fixed(fe_id: int, ano_mes: str) -> str:
    return f"fixed:{fe_id}:{ano_mes}"


def transaction_key_subscription(sub_id: int, ano_mes: str) -> str:
    return f"subscription:{sub_id}:{ano_mes}"


def transaction_key_installment(inst_id: int, ano_mes: str) -> str:
    return f"installment:{inst_id}:{ano_mes}"


def transaction_key_income(src_id: int, ano_mes: str) -> str:
    return f"income:{src_id}:{ano_mes}"


def transaction_key_import_credit(batch_id: int, external_id: str) -> str:
    return f"import_credit:{batch_id}:{external_id}"


def current_balance(account_id: int, conn: Optional[sqlite3.Connection] = None) -> float:
    """Saldo até hoje: saldo_inicial + soma das movimentações com data <= hoje."""

    def _run(c: sqlite3.Connection) -> float:
        row = c.execute(
            "SELECT saldo_inicial FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if not row:
            return 0.0
        base = float(row["saldo_inicial"] or 0)
        r2 = c.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS t
              FROM account_transactions
             WHERE account_id = ?
               AND date(data) <= date('now', 'localtime')
            """,
            (account_id,),
        ).fetchone()
        return round(base + float(r2["t"] or 0), 2)

    if conn is not None:
        return _run(conn)
    with transaction() as c:
        return _run(c)


def sum_balances(conn: Optional[sqlite3.Connection] = None) -> float:
    """Soma dos saldos atuais de todas as contas."""

    def _run(c: sqlite3.Connection) -> float:
        rows = c.execute("SELECT id FROM accounts").fetchall()
        total = 0.0
        for r in rows:
            total += current_balance(int(r["id"]), c)
        return round(total, 2)

    if conn is not None:
        return _run(conn)
    with transaction() as c:
        return _run(c)


def post_adjustment(
    account_id: int,
    valor_delta: float,
    data: str,
    descricao: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Ajuste manual (+ ou -)."""
    key = f"adjustment:{uuid.uuid4().hex}"
    return upsert_transaction(
        account_id,
        valor_delta,
        data,
        "ajuste",
        key,
        descricao,
        conn=conn,
    )


def list_all() -> List[Account]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.nome, a.observacao, a.saldo_inicial,
                   a.saldo_inicial + COALESCE((
                     SELECT SUM(t.valor)
                       FROM account_transactions t
                      WHERE t.account_id = a.id
                        AND date(t.data) <= date('now', 'localtime')
                   ), 0) AS saldo_atual
              FROM accounts a
             ORDER BY a.nome COLLATE NOCASE
            """
        ).fetchall()
    return [Account.from_row(r) for r in rows]


def get(account_id: int) -> Optional[Account]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT a.id, a.nome, a.observacao, a.saldo_inicial,
                   a.saldo_inicial + COALESCE((
                     SELECT SUM(t.valor)
                       FROM account_transactions t
                      WHERE t.account_id = a.id
                        AND date(t.data) <= date('now', 'localtime')
                   ), 0) AS saldo_atual
              FROM accounts a
             WHERE a.id = ?
            """,
            (account_id,),
        ).fetchone()
    return Account.from_row(row) if row else None


def create(acc: Account) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO accounts (nome, observacao, saldo_inicial)
            VALUES (?, ?, ?)
            """,
            (acc.nome.strip(), acc.observacao, float(acc.saldo_inicial)),
        )
        return int(cur.lastrowid)


def update(acc: Account) -> None:
    if acc.id is None:
        raise ValueError("Conta sem id")
    with transaction() as conn:
        conn.execute(
            """
            UPDATE accounts
               SET nome = ?, observacao = ?, saldo_inicial = ?
             WHERE id = ?
            """,
            (acc.nome.strip(), acc.observacao, float(acc.saldo_inicial), acc.id),
        )


def delete(account_id: int) -> None:
    if count_references(account_id) > 0:
        raise ValueError(
            "Esta conta está em uso em pagamentos, assinaturas ou cartões vinculados. "
            "Altere os registros antes de excluir."
        )
    with transaction() as conn:
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))


def count_references(account_id: int) -> int:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT (
                SELECT COUNT(*) FROM payments WHERE conta_id = ?
            ) + (
                SELECT COUNT(*) FROM subscriptions WHERE account_id = ?
            ) + (
                SELECT COUNT(*) FROM cards WHERE account_id = ?
            ) + (
                SELECT COUNT(*) FROM fixed_expenses WHERE conta_id = ?
            ) + (
                SELECT COUNT(*) FROM investments WHERE banco_id = ?
            ) + (
                SELECT COUNT(*) FROM income_sources WHERE account_id = ?
            ) + (
                SELECT COUNT(*) FROM installments WHERE account_id = ?
            ) AS n
            """,
            (
                account_id,
                account_id,
                account_id,
                account_id,
                account_id,
                account_id,
                account_id,
            ),
        ).fetchone()
    return int(row["n"] or 0) if row else 0


def sum_debits_in_month(ano_mes: str, conn: Optional[sqlite3.Connection] = None) -> float:
    """Soma valores negativos (saídas) no mês YYYY-MM em todas as contas."""

    def _run(c: sqlite3.Connection) -> float:
        row = c.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS t
              FROM account_transactions
             WHERE substr(data, 1, 7) = ?
               AND valor < 0
            """,
            (ano_mes,),
        ).fetchone()
        return round(float(row["t"] or 0), 2)

    if conn is not None:
        return _run(conn)
    with transaction() as c:
        return _run(c)
