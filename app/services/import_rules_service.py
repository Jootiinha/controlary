"""Regras de auto-categorização para importação (contains / regex)."""
from __future__ import annotations

import re
from typing import List, Optional

from app.database.connection import transaction


def list_ordered() -> list[tuple[int, str, str, int, int]]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT id, padrao, padrao_tipo, category_id, prioridade
              FROM import_rules
             ORDER BY prioridade DESC, id ASC
            """
        ).fetchall()
    return [
        (int(r["id"]), r["padrao"], r["padrao_tipo"], int(r["category_id"]), int(r["prioridade"]))
        for r in rows
    ]


def match_category(descricao: str) -> Optional[int]:
    if not descricao.strip():
        return None
    low = descricao.lower()
    for _rid, padrao, tipo, cat_id, _prio in list_ordered():
        if tipo == "contains":
            if padrao.lower() in low:
                return cat_id
        elif tipo == "regex":
            try:
                if re.search(padrao, descricao, re.IGNORECASE):
                    return cat_id
            except re.error:
                continue
    return None


def insert_rule(
    padrao: str,
    padrao_tipo: str,
    category_id: int,
    prioridade: int = 0,
) -> int:
    if padrao_tipo not in ("contains", "regex"):
        raise ValueError("Tipo de padrão inválido")
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO import_rules (padrao, padrao_tipo, category_id, prioridade)
            VALUES (?, ?, ?, ?)
            """,
            (padrao.strip(), padrao_tipo, category_id, prioridade),
        )
        return int(cur.lastrowid)


def delete_rule(rule_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM import_rules WHERE id = ?", (rule_id,))


def list_all() -> List[dict]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.padrao, r.padrao_tipo, r.category_id, r.prioridade, c.nome AS categoria_nome
              FROM import_rules r
              JOIN categories c ON c.id = r.category_id
             ORDER BY r.prioridade DESC, r.id ASC
            """
        ).fetchall()
    return [dict(r) for r in rows]
