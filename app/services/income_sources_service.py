"""CRUD e agregações para fontes de renda mensal."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from app.database.connection import transaction
from app.models.income_source import IncomeSource
from app.services import accounts_service


def list_all() -> List[IncomeSource]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT i.*, a.nome AS conta_nome
              FROM income_sources i
              LEFT JOIN accounts a ON a.id = i.account_id
             ORDER BY CASE WHEN i.ativo = 1 THEN 0 ELSE 1 END,
                      i.nome COLLATE NOCASE
            """
        ).fetchall()
    return [IncomeSource.from_row(r) for r in rows]


def get(source_id: int) -> Optional[IncomeSource]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT i.*, a.nome AS conta_nome
              FROM income_sources i
              LEFT JOIN accounts a ON a.id = i.account_id
             WHERE i.id = ?
            """,
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


def sum_expected_receipts_rest_of_month(ano_mes: str) -> float:
    """Entradas ainda esperadas no mês: dia >= hoje e não marcadas como recebidas."""
    today = date.today()
    cur_mes = f"{today.year:04d}-{today.month:02d}"
    if ano_mes != cur_mes:
        return 0.0
    d0 = today.day
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT i.id, i.valor_mensal, i.dia_recebimento
              FROM income_sources i
             WHERE i.ativo = 1
            """
        ).fetchall()
        total = 0.0
        for r in rows:
            if int(r["dia_recebimento"] or 5) < d0:
                continue
            mm = conn.execute(
                """
                SELECT status FROM income_months
                 WHERE income_source_id = ? AND ano_mes = ?
                """,
                (int(r["id"]), ano_mes),
            ).fetchone()
            if mm and mm["status"] == "recebido":
                continue
            total += float(r["valor_mensal"] or 0)
    return round(total, 2)


def create(src: IncomeSource) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO income_sources (
                nome, valor_mensal, ativo, dia_recebimento, account_id, observacao
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                src.nome,
                src.valor_mensal,
                1 if src.ativo else 0,
                src.dia_recebimento,
                src.account_id,
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
               SET nome = ?, valor_mensal = ?, ativo = ?, dia_recebimento = ?,
                   account_id = ?, observacao = ?
             WHERE id = ?
            """,
            (
                src.nome,
                src.valor_mensal,
                1 if src.ativo else 0,
                src.dia_recebimento,
                src.account_id,
                src.observacao,
                src.id,
            ),
        )


def delete(source_id: int) -> None:
    with transaction() as conn:
        accounts_service.remove_transaction_keys_like_prefix(
            f"income:{source_id}:", conn=conn
        )
        conn.execute("DELETE FROM income_sources WHERE id = ?", (source_id,))
