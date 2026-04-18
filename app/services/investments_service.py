"""Investimentos e snapshots de valor."""
from __future__ import annotations

from typing import List, Optional

from app.database.connection import transaction
from app.models.investment import Investment, InvestmentSnapshot


def list_all(include_inactive: bool = False) -> List[Investment]:
    with transaction() as conn:
        q = """
            SELECT i.*, a.nome AS banco_nome, cat.nome AS categoria_nome
              FROM investments i
              JOIN accounts a ON a.id = i.banco_id
              LEFT JOIN categories cat ON cat.id = i.category_id
        """
        if not include_inactive:
            q += " WHERE i.ativo = 1"
        q += " ORDER BY i.nome COLLATE NOCASE"
        rows = conn.execute(q).fetchall()
    return [Investment.from_row(r) for r in rows]


def get(inv_id: int) -> Optional[Investment]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT i.*, a.nome AS banco_nome, cat.nome AS categoria_nome
              FROM investments i
              JOIN accounts a ON a.id = i.banco_id
              LEFT JOIN categories cat ON cat.id = i.category_id
             WHERE i.id = ?
            """,
            (inv_id,),
        ).fetchone()
    return Investment.from_row(row) if row else None


def create(inv: Investment) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO investments (
                banco_id, nome, tipo, valor_aplicado, rendimento_percentual_aa,
                data_aplicacao, data_vencimento, category_id, observacao, ativo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inv.banco_id,
                inv.nome.strip(),
                inv.tipo,
                inv.valor_aplicado,
                inv.rendimento_percentual_aa,
                inv.data_aplicacao,
                inv.data_vencimento,
                inv.category_id,
                inv.observacao,
                1 if inv.ativo else 0,
            ),
        )
        return int(cur.lastrowid)


def update(inv: Investment) -> None:
    if inv.id is None:
        raise ValueError("Investimento sem id")
    with transaction() as conn:
        conn.execute(
            """
            UPDATE investments
               SET banco_id = ?, nome = ?, tipo = ?, valor_aplicado = ?,
                   rendimento_percentual_aa = ?, data_aplicacao = ?, data_vencimento = ?,
                   category_id = ?, observacao = ?, ativo = ?
             WHERE id = ?
            """,
            (
                inv.banco_id,
                inv.nome.strip(),
                inv.tipo,
                inv.valor_aplicado,
                inv.rendimento_percentual_aa,
                inv.data_aplicacao,
                inv.data_vencimento,
                inv.category_id,
                inv.observacao,
                1 if inv.ativo else 0,
                inv.id,
            ),
        )


def delete(inv_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM investments WHERE id = ?", (inv_id,))


def total_aplicado() -> float:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_aplicado), 0) AS t
              FROM investments
             WHERE ativo = 1
            """
        ).fetchone()
    return float(row["t"] or 0)


def add_snapshot(inv_id: int, data: str, valor_atual: float) -> None:
    with transaction() as conn:
        conn.execute(
            """
            DELETE FROM investment_snapshots
             WHERE investment_id = ? AND data = ?
            """,
            (inv_id, data),
        )
        conn.execute(
            """
            INSERT INTO investment_snapshots (investment_id, data, valor_atual)
            VALUES (?, ?, ?)
            """,
            (inv_id, data, valor_atual),
        )


def list_snapshots(inv_id: int) -> List[InvestmentSnapshot]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT investment_id, data, valor_atual
              FROM investment_snapshots
             WHERE investment_id = ?
             ORDER BY date(data)
            """,
            (inv_id,),
        ).fetchall()
    return [InvestmentSnapshot.from_row(r) for r in rows]
