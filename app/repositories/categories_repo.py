"""Categorias globais."""
from __future__ import annotations

import sqlite3
from typing import List, Optional


def list_fixed_for_mapping(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT f.nome AS nome, cat.nome AS catn, f.ativo
          FROM fixed_expenses f
          LEFT JOIN categories cat ON cat.id = f.category_id
         ORDER BY f.nome COLLATE NOCASE
        """
    ).fetchall()


def list_subscriptions_for_mapping(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT s.nome AS nome,
               COALESCE(cat.nome, NULLIF(TRIM(s.categoria), ''), '—') AS catn,
               s.status
          FROM subscriptions s
          LEFT JOIN categories cat ON cat.id = s.category_id
         ORDER BY s.nome COLLATE NOCASE
        """
    ).fetchall()


def list_installments_for_mapping(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.nome_fatura AS nome,
               COALESCE(cat.nome, '—') AS catn,
               i.status,
               COALESCE(c.nome, a.nome, NULLIF(TRIM(i.cartao), ''), '—') AS meio
          FROM installments i
          LEFT JOIN cards c ON c.id = i.cartao_id
          LEFT JOIN accounts a ON a.id = i.account_id
          LEFT JOIN categories cat ON cat.id = i.category_id
         ORDER BY i.nome_fatura COLLATE NOCASE
        """
    ).fetchall()


def list_investments_for_mapping(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.nome AS nome,
               COALESCE(cat.nome, '—') AS catn,
               i.tipo,
               i.ativo
          FROM investments i
          LEFT JOIN categories cat ON cat.id = i.category_id
         ORDER BY i.nome COLLATE NOCASE
        """
    ).fetchall()


def list_all(conn: sqlite3.Connection, include_inactive: bool) -> List[sqlite3.Row]:
    if include_inactive:
        return conn.execute(
            "SELECT * FROM categories ORDER BY nome COLLATE NOCASE"
        ).fetchall()
    return conn.execute(
        "SELECT * FROM categories WHERE ativo = 1 ORDER BY nome COLLATE NOCASE"
    ).fetchall()


def get(conn: sqlite3.Connection, cat_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM categories WHERE id = ?", (cat_id,)
    ).fetchone()


def get_by_name(conn: sqlite3.Connection, nome: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM categories WHERE nome = ? COLLATE NOCASE LIMIT 1",
        (nome.strip(),),
    ).fetchone()


def insert(
    conn: sqlite3.Connection,
    *,
    nome: str,
    tipo_sugerido: Optional[str],
    cor: Optional[str],
    ativo: int,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO categories (nome, tipo_sugerido, cor, ativo)
        VALUES (?, ?, ?, ?)
        """,
        (nome, tipo_sugerido, cor, ativo),
    )
    return int(cur.lastrowid)


def update(
    conn: sqlite3.Connection,
    *,
    cat_id: int,
    nome: str,
    tipo_sugerido: Optional[str],
    cor: Optional[str],
    ativo: int,
) -> None:
    conn.execute(
        """
        UPDATE categories
           SET nome = ?, tipo_sugerido = ?, cor = ?, ativo = ?
         WHERE id = ?
        """,
        (nome, tipo_sugerido, cor, ativo, cat_id),
    )


def delete(conn: sqlite3.Connection, cat_id: int) -> None:
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
