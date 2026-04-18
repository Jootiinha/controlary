"""CRUD e agregações para fontes de renda mensal."""
from __future__ import annotations

from typing import List, Optional

from app.database.connection import transaction
from app.models.income_source import IncomeSource


def list_all() -> List[IncomeSource]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT * FROM income_sources
             ORDER BY CASE WHEN ativo = 1 THEN 0 ELSE 1 END,
                      nome COLLATE NOCASE
            """
        ).fetchall()
    return [IncomeSource.from_row(r) for r in rows]


def get(source_id: int) -> Optional[IncomeSource]:
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM income_sources WHERE id = ?",
            (source_id,),
        ).fetchone()
    return IncomeSource.from_row(row) if row else None


def sum_active_monthly() -> float:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_mensal), 0) AS total
              FROM income_sources
             WHERE ativo = 1
            """
        ).fetchone()
    return float(row["total"] or 0)


def create(src: IncomeSource) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO income_sources (nome, valor_mensal, ativo, dia_recebimento, observacao)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                src.nome,
                src.valor_mensal,
                1 if src.ativo else 0,
                src.dia_recebimento,
                src.observacao,
            ),
        )
        return int(cur.lastrowid)


def update(src: IncomeSource) -> None:
    if src.id is None:
        raise ValueError("Fonte de renda sem id não pode ser atualizada")
    with transaction() as conn:
        conn.execute(
            """
            UPDATE income_sources
               SET nome = ?, valor_mensal = ?, ativo = ?, dia_recebimento = ?, observacao = ?
             WHERE id = ?
            """,
            (
                src.nome,
                src.valor_mensal,
                1 if src.ativo else 0,
                src.dia_recebimento,
                src.observacao,
                src.id,
            ),
        )


def delete(source_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM income_sources WHERE id = ?", (source_id,))
