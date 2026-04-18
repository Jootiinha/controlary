"""CRUD de contas bancárias."""
from __future__ import annotations

from typing import List, Optional

from app.database.connection import transaction
from app.models.account import Account


def list_all() -> List[Account]:
    with transaction() as conn:
        rows = conn.execute(
            "SELECT * FROM accounts ORDER BY nome COLLATE NOCASE"
        ).fetchall()
    return [Account.from_row(r) for r in rows]


def get(account_id: int) -> Optional[Account]:
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
    return Account.from_row(row) if row else None


def create(acc: Account) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, observacao) VALUES (?, ?)",
            (acc.nome.strip(), acc.observacao),
        )
        return int(cur.lastrowid)


def update(acc: Account) -> None:
    if acc.id is None:
        raise ValueError("Conta sem id")
    with transaction() as conn:
        conn.execute(
            "UPDATE accounts SET nome = ?, observacao = ? WHERE id = ?",
            (acc.nome.strip(), acc.observacao, acc.id),
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
            ) AS n
            """,
            (account_id, account_id, account_id),
        ).fetchone()
    return int(row["n"] or 0) if row else 0
