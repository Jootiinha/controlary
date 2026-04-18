"""CRUD de categorias globais."""
from __future__ import annotations

from typing import List, Optional

from app.database.connection import transaction
from app.models.category import Category


def list_all(include_inactive: bool = False) -> List[Category]:
    with transaction() as conn:
        if include_inactive:
            rows = conn.execute(
                "SELECT * FROM categories ORDER BY nome COLLATE NOCASE"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM categories WHERE ativo = 1 ORDER BY nome COLLATE NOCASE"
            ).fetchall()
    return [Category.from_row(r) for r in rows]


def get(cat_id: int) -> Optional[Category]:
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM categories WHERE id = ?", (cat_id,)
        ).fetchone()
    return Category.from_row(row) if row else None


def get_by_name(nome: str) -> Optional[Category]:
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM categories WHERE nome = ? COLLATE NOCASE LIMIT 1",
            (nome.strip(),),
        ).fetchone()
    return Category.from_row(row) if row else None


def create(cat: Category) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO categories (nome, tipo_sugerido, cor, ativo)
            VALUES (?, ?, ?, ?)
            """,
            (
                cat.nome.strip(),
                cat.tipo_sugerido,
                cat.cor,
                1 if cat.ativo else 0,
            ),
        )
        return int(cur.lastrowid)


def update(cat: Category) -> None:
    if cat.id is None:
        raise ValueError("Categoria sem id")
    with transaction() as conn:
        conn.execute(
            """
            UPDATE categories
               SET nome = ?, tipo_sugerido = ?, cor = ?, ativo = ?
             WHERE id = ?
            """,
            (
                cat.nome.strip(),
                cat.tipo_sugerido,
                cat.cor,
                1 if cat.ativo else 0,
                cat.id,
            ),
        )


def delete(cat_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
