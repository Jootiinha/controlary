"""Gastos fixos e competência mensal."""
from __future__ import annotations

import sqlite3
from typing import List, Optional


def status_row(conn: sqlite3.Connection, fe_id: int, ano_mes: str) -> Optional[str]:
    row = conn.execute(
        """
        SELECT status FROM fixed_expense_months
         WHERE fixed_expense_id = ? AND ano_mes = ?
        """,
        (fe_id, ano_mes),
    ).fetchone()
    return row["status"] if row else None


def fetch_valor_efetivo_month(conn: sqlite3.Connection, fe_id: int, ano_mes: str) -> Optional[float]:
    row = conn.execute(
        """
        SELECT valor_efetivo FROM fixed_expense_months
         WHERE fixed_expense_id = ? AND ano_mes = ?
        """,
        (fe_id, ano_mes),
    ).fetchone()
    if not row or row["valor_efetivo"] is None:
        return None
    return float(row["valor_efetivo"])


def fetch_fixed_for_month_apply(conn: sqlite3.Connection, fe_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT valor_mensal, conta_id, dia_referencia
          FROM fixed_expenses
         WHERE id = ?
        """,
        (fe_id,),
    ).fetchone()


def exists_month_row(conn: sqlite3.Connection, fe_id: int, ano_mes: str) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM fixed_expense_months
         WHERE fixed_expense_id = ? AND ano_mes = ?
        """,
        (fe_id, ano_mes),
    ).fetchone()
    return row is not None


def upsert_month_row(
    conn: sqlite3.Connection,
    fe_id: int,
    ano_mes: str,
    status: str,
    valor_gravado: Optional[float],
) -> None:
    row = conn.execute(
        """
        SELECT 1 FROM fixed_expense_months
         WHERE fixed_expense_id = ? AND ano_mes = ?
        """,
        (fe_id, ano_mes),
    ).fetchone()
    if row:
        conn.execute(
            """
            UPDATE fixed_expense_months SET status = ?, valor_efetivo = ?
             WHERE fixed_expense_id = ? AND ano_mes = ?
            """,
            (status, valor_gravado, fe_id, ano_mes),
        )
    else:
        conn.execute(
            """
            INSERT INTO fixed_expense_months (fixed_expense_id, ano_mes, status, valor_efetivo)
            VALUES (?, ?, ?, ?)
            """,
            (fe_id, ano_mes, status, valor_gravado),
        )


def list_active(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT f.*, a.nome AS conta_nome, cat.nome AS categoria_nome
          FROM fixed_expenses f
          LEFT JOIN accounts a ON a.id = f.conta_id
          LEFT JOIN categories cat ON cat.id = f.category_id
         WHERE f.ativo = 1
         ORDER BY f.nome COLLATE NOCASE
        """
    ).fetchall()


def list_all(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT f.*, a.nome AS conta_nome, cat.nome AS categoria_nome
          FROM fixed_expenses f
          LEFT JOIN accounts a ON a.id = f.conta_id
          LEFT JOIN categories cat ON cat.id = f.category_id
         ORDER BY f.ativo DESC, f.nome COLLATE NOCASE
        """
    ).fetchall()


def get(conn: sqlite3.Connection, fe_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT f.*, a.nome AS conta_nome, cat.nome AS categoria_nome
          FROM fixed_expenses f
          LEFT JOIN accounts a ON a.id = f.conta_id
          LEFT JOIN categories cat ON cat.id = f.category_id
         WHERE f.id = ?
        """,
        (fe_id,),
    ).fetchone()


def insert(
    conn: sqlite3.Connection,
    *,
    nome: str,
    valor_mensal: float,
    dia_referencia: int,
    forma_pagamento: str,
    conta_id: Optional[int],
    observacao: Optional[str],
    ativo: int,
    category_id: Optional[int],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO fixed_expenses (
            nome, valor_mensal, dia_referencia, forma_pagamento,
            conta_id, observacao, ativo, category_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            valor_mensal,
            dia_referencia,
            forma_pagamento,
            conta_id,
            observacao,
            ativo,
            category_id,
        ),
    )
    return int(cur.lastrowid)


def update(
    conn: sqlite3.Connection,
    *,
    fe_id: int,
    nome: str,
    valor_mensal: float,
    dia_referencia: int,
    forma_pagamento: str,
    conta_id: Optional[int],
    observacao: Optional[str],
    ativo: int,
    category_id: Optional[int],
) -> None:
    conn.execute(
        """
        UPDATE fixed_expenses
           SET nome = ?, valor_mensal = ?, dia_referencia = ?, forma_pagamento = ?,
               conta_id = ?, observacao = ?, ativo = ?, category_id = ?
         WHERE id = ?
        """,
        (
            nome,
            valor_mensal,
            dia_referencia,
            forma_pagamento,
            conta_id,
            observacao,
            ativo,
            category_id,
            fe_id,
        ),
    )


def delete(conn: sqlite3.Connection, fe_id: int) -> None:
    conn.execute("DELETE FROM fixed_expenses WHERE id = ?", (fe_id,))


def sum_unpaid_for_month(conn: sqlite3.Connection, ano_mes: str) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT f.valor_mensal, m.status
          FROM fixed_expenses f
          LEFT JOIN fixed_expense_months m
            ON m.fixed_expense_id = f.id AND m.ano_mes = ?
         WHERE f.ativo = 1
        """,
        (ano_mes,),
    ).fetchall()


def sum_paid_for_month_row(conn: sqlite3.Connection, ano_mes: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT COALESCE(SUM(COALESCE(m.valor_efetivo, f.valor_mensal)), 0) AS t
          FROM fixed_expenses f
          JOIN fixed_expense_months m
            ON m.fixed_expense_id = f.id AND m.ano_mes = ?
         WHERE f.ativo = 1 AND m.status = 'pago'
        """,
        (ano_mes,),
    ).fetchone()


def count_active(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM fixed_expenses WHERE ativo = 1"
    ).fetchone()
    return int(row["n"] or 0) if row else 0
