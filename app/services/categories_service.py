"""CRUD de categorias globais."""
from __future__ import annotations

import sqlite3
from typing import List, Optional, Tuple

from app.database.connection import use
from app.events import app_events
from app.models.category import Category
from app.repositories import categories_repo


def list_expense_category_mappings(
    conn: Optional[sqlite3.Connection] = None,
) -> List[Tuple[str, str, str, str]]:
    """Linhas (tipo, nome, categoria, detalhe) para cadastros com categoria."""
    out: list[tuple[str, str, str, str, list[object]]] = []
    with use(conn) as c:
        for r in categories_repo.list_fixed_for_mapping(c):
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
        for r in categories_repo.list_subscriptions_for_mapping(c):
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
        for r in categories_repo.list_installments_for_mapping(c):
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
        for r in categories_repo.list_investments_for_mapping(c):
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


def list_all(
    include_inactive: bool = False, conn: Optional[sqlite3.Connection] = None
) -> List[Category]:
    with use(conn) as c:
        rows = categories_repo.list_all(c, include_inactive)
    return [Category.from_row(r) for r in rows]


def get(cat_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Category]:
    with use(conn) as c:
        row = categories_repo.get(c, cat_id)
    return Category.from_row(row) if row else None


def get_or_unknown(
    cat_id: Optional[int], label: str = "—", conn: Optional[sqlite3.Connection] = None
) -> Category:
    if cat_id is None:
        return Category.unknown(label)
    cat = get(cat_id, conn=conn)
    return cat if cat is not None else Category.unknown(label)


def get_by_name(nome: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Category]:
    with use(conn) as c:
        row = categories_repo.get_by_name(c, nome)
    return Category.from_row(row) if row else None


def create(cat: Category, conn: Optional[sqlite3.Connection] = None) -> int:
    with use(conn) as c:
        pid = categories_repo.insert(
            c,
            nome=cat.nome.strip(),
            tipo_sugerido=cat.tipo_sugerido,
            cor=cat.cor,
            ativo=1 if cat.ativo else 0,
        )
    app_events().categories_changed.emit()
    return pid


def update(cat: Category, conn: Optional[sqlite3.Connection] = None) -> None:
    if cat.id is None:
        raise ValueError("Categoria sem id")
    with use(conn) as c:
        categories_repo.update(
            c,
            cat_id=int(cat.id),
            nome=cat.nome.strip(),
            tipo_sugerido=cat.tipo_sugerido,
            cor=cat.cor,
            ativo=1 if cat.ativo else 0,
        )
    app_events().categories_changed.emit()


def delete(cat_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        categories_repo.delete(c, cat_id)
    app_events().categories_changed.emit()
