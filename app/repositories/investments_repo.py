"""SQL puro para investments e investment_snapshots."""
from __future__ import annotations

import sqlite3
from typing import Optional


def list_all(conn: sqlite3.Connection, include_inactive: bool) -> list[sqlite3.Row]:
    q = """
        SELECT i.*, a.nome AS banco_nome, cat.nome AS categoria_nome
          FROM investments i
          JOIN accounts a ON a.id = i.banco_id
          LEFT JOIN categories cat ON cat.id = i.category_id
    """
    if not include_inactive:
        q += " WHERE i.ativo = 1"
    q += " ORDER BY i.nome COLLATE NOCASE"
    return conn.execute(q).fetchall()


def get_row(conn: sqlite3.Connection, inv_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, a.nome AS banco_nome, cat.nome AS categoria_nome
          FROM investments i
          JOIN accounts a ON a.id = i.banco_id
          LEFT JOIN categories cat ON cat.id = i.category_id
         WHERE i.id = ?
        """,
        (inv_id,),
    ).fetchone()


def insert_investment(
    conn: sqlite3.Connection,
    *,
    banco_id: int,
    nome: str,
    tipo: str,
    valor_aplicado: float,
    rendimento_percentual_aa: Optional[float],
    data_aplicacao: str,
    data_vencimento: Optional[str],
    category_id: Optional[int],
    observacao: Optional[str],
    ativo: int,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO investments (
            banco_id, nome, tipo, valor_aplicado, rendimento_percentual_aa,
            data_aplicacao, data_vencimento, category_id, observacao, ativo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            banco_id,
            nome,
            tipo,
            valor_aplicado,
            rendimento_percentual_aa,
            data_aplicacao,
            data_vencimento,
            category_id,
            observacao,
            ativo,
        ),
    )
    return int(cur.lastrowid)


def update_investment(
    conn: sqlite3.Connection,
    *,
    inv_id: int,
    banco_id: int,
    nome: str,
    tipo: str,
    valor_aplicado: float,
    rendimento_percentual_aa: Optional[float],
    data_aplicacao: str,
    data_vencimento: Optional[str],
    category_id: Optional[int],
    observacao: Optional[str],
    ativo: int,
) -> None:
    conn.execute(
        """
        UPDATE investments
           SET banco_id = ?, nome = ?, tipo = ?, valor_aplicado = ?,
               rendimento_percentual_aa = ?, data_aplicacao = ?, data_vencimento = ?,
               category_id = ?, observacao = ?, ativo = ?
         WHERE id = ?
        """,
        (
            banco_id,
            nome,
            tipo,
            valor_aplicado,
            rendimento_percentual_aa,
            data_aplicacao,
            data_vencimento,
            category_id,
            observacao,
            ativo,
            inv_id,
        ),
    )


def delete_investment(conn: sqlite3.Connection, inv_id: int) -> None:
    conn.execute("DELETE FROM investments WHERE id = ?", (inv_id,))


def sum_aplicado_ativo(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor_aplicado), 0) AS t
          FROM investments
         WHERE ativo = 1
        """
    ).fetchone()
    return float(row["t"] or 0)


def delete_snapshot_on_date(
    conn: sqlite3.Connection, inv_id: int, data: str
) -> None:
    conn.execute(
        """
        DELETE FROM investment_snapshots
         WHERE investment_id = ? AND data = ?
        """,
        (inv_id, data),
    )


def insert_snapshot(
    conn: sqlite3.Connection, inv_id: int, data: str, valor_atual: float
) -> None:
    conn.execute(
        """
        INSERT INTO investment_snapshots (investment_id, data, valor_atual)
        VALUES (?, ?, ?)
        """,
        (inv_id, data, valor_atual),
    )


def list_snapshots(conn: sqlite3.Connection, inv_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT investment_id, data, valor_atual
          FROM investment_snapshots
         WHERE investment_id = ?
         ORDER BY date(data)
        """,
        (inv_id,),
    ).fetchall()


def fetch_valor_aplicado_data(conn: sqlite3.Connection, inv_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT valor_aplicado, data_aplicacao
          FROM investments
         WHERE id = ?
        """,
        (inv_id,),
    ).fetchone()


def list_snapshots_ordered(conn: sqlite3.Connection, inv_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT data, valor_atual
          FROM investment_snapshots
         WHERE investment_id = ?
         ORDER BY date(data)
        """,
        (inv_id,),
    ).fetchall()


def update_rendimento_aa(conn: sqlite3.Connection, inv_id: int, pct: float) -> None:
    conn.execute(
        "UPDATE investments SET rendimento_percentual_aa = ? WHERE id = ?",
        (pct, inv_id),
    )
