"""CRUD de categorias globais."""
from __future__ import annotations

from typing import List, Optional, Tuple

from app.database.connection import transaction
from app.models.category import Category


def list_expense_category_mappings() -> List[Tuple[str, str, str, str]]:
    """Linhas (tipo, nome, categoria, detalhe) para cadastros com categoria.

    Inclui gastos fixos, assinaturas, parcelamentos e investimentos.
    Assinaturas usam categoria global ou texto legado quando não houver ``category_id``.
    """
    out: list[tuple[str, str, str, str, list[object]]] = []
    with transaction() as conn:
        for r in conn.execute(
            """
            SELECT f.nome AS nome, cat.nome AS catn, f.ativo
              FROM fixed_expenses f
              LEFT JOIN categories cat ON cat.id = f.category_id
             ORDER BY f.nome COLLATE NOCASE
            """
        ):
            cat = (r["catn"] or "").strip() or "—"
            det = "" if r["ativo"] else "Inativo"
            out.append(
                (
                    "Gasto fixo",
                    r["nome"],
                    cat,
                    det,
                    ["Gasto fixo", (r["nome"] or "").casefold(), cat.casefold(), det.casefold()],
                )
            )
        for r in conn.execute(
            """
            SELECT s.nome AS nome,
                   COALESCE(cat.nome, NULLIF(TRIM(s.categoria), ''), '—') AS catn,
                   s.status
              FROM subscriptions s
              LEFT JOIN categories cat ON cat.id = s.category_id
             ORDER BY s.nome COLLATE NOCASE
            """
        ):
            cat = (r["catn"] or "").strip() or "—"
            st = r["status"] or ""
            out.append(
                (
                    "Assinatura",
                    r["nome"],
                    cat,
                    st,
                    ["Assinatura", (r["nome"] or "").casefold(), cat.casefold(), st.casefold()],
                )
            )
        for r in conn.execute(
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
        ):
            cat = (r["catn"] or "").strip() or "—"
            meio = r["meio"] or "—"
            st = r["status"] or ""
            det = f"{meio} · {st}"
            out.append(
                (
                    "Parcelamento",
                    r["nome"],
                    cat,
                    det,
                    [
                        "Parcelamento",
                        (r["nome"] or "").casefold(),
                        cat.casefold(),
                        det.casefold(),
                    ],
                )
            )
        for r in conn.execute(
            """
            SELECT i.nome AS nome,
                   COALESCE(cat.nome, '—') AS catn,
                   i.tipo,
                   i.ativo
              FROM investments i
              LEFT JOIN categories cat ON cat.id = i.category_id
             ORDER BY i.nome COLLATE NOCASE
            """
        ):
            cat = (r["catn"] or "").strip() or "—"
            tipo_inv = (r["tipo"] or "").strip()
            det = tipo_inv + ("" if r["ativo"] else " · inativo")
            out.append(
                (
                    "Investimento",
                    r["nome"],
                    cat,
                    det,
                    [
                        "Investimento",
                        (r["nome"] or "").casefold(),
                        cat.casefold(),
                        det.casefold(),
                    ],
                )
            )
    out.sort(
        key=lambda row: (
            (row[4][2] or "").casefold(),
            (row[4][0] or "").casefold(),
            (row[4][1] or "").casefold(),
        )
    )
    return [(a, b, c, d) for a, b, c, d, _ in out]


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
