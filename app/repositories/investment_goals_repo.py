"""SQL puro para investment_goals."""
from __future__ import annotations

import sqlite3
from typing import Optional


def list_all(conn: sqlite3.Connection, include_inactive: bool) -> list[sqlite3.Row]:
    q = """
        SELECT g.*, cat.nome AS categoria_nome
          FROM investment_goals g
          LEFT JOIN categories cat ON cat.id = g.category_id
    """
    if not include_inactive:
        q += " WHERE g.ativo = 1"
    q += " ORDER BY g.nome COLLATE NOCASE"
    return conn.execute(q).fetchall()


def get_row(conn: sqlite3.Connection, goal_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT g.*, cat.nome AS categoria_nome
          FROM investment_goals g
          LEFT JOIN categories cat ON cat.id = g.category_id
         WHERE g.id = ?
        """,
        (goal_id,),
    ).fetchone()


def insert_goal(
    conn: sqlite3.Connection,
    *,
    nome: str,
    valor_alvo: float,
    category_id: Optional[int],
    data_alvo: Optional[str],
    observacao: Optional[str],
    ativo: int,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO investment_goals (
            nome, valor_alvo, category_id, data_alvo, observacao, ativo
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (nome, valor_alvo, category_id, data_alvo, observacao, ativo),
    )
    return int(cur.lastrowid)


def update_goal(
    conn: sqlite3.Connection,
    *,
    goal_id: int,
    nome: str,
    valor_alvo: float,
    category_id: Optional[int],
    data_alvo: Optional[str],
    observacao: Optional[str],
    ativo: int,
) -> None:
    conn.execute(
        """
        UPDATE investment_goals
           SET nome = ?, valor_alvo = ?, category_id = ?, data_alvo = ?,
               observacao = ?, ativo = ?
         WHERE id = ?
        """,
        (nome, valor_alvo, category_id, data_alvo, observacao, ativo, goal_id),
    )


def delete_goal(conn: sqlite3.Connection, goal_id: int) -> None:
    conn.execute("DELETE FROM investment_goals WHERE id = ?", (goal_id,))
