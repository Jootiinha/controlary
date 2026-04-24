"""SQL puro para income_sources e consultas auxiliares."""
from __future__ import annotations

import sqlite3
from typing import Optional


def avulsa_duplicate(
    conn: sqlite3.Connection,
    nome: str,
    mes: str,
    exclude_id: Optional[int],
) -> bool:
    q = """
        SELECT 1 FROM income_sources
         WHERE tipo = 'avulsa' AND mes_referencia = ? AND nome = ? COLLATE NOCASE
    """
    params: list = [mes, nome.strip()]
    if exclude_id is not None:
        q += " AND id != ?"
        params.append(exclude_id)
    return conn.execute(q, params).fetchone() is not None


def count_month_rows(conn: sqlite3.Connection, source_id: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS n FROM income_months
         WHERE income_source_id = ?
        """,
        (source_id,),
    ).fetchone()
    return int(row["n"] or 0) if row else 0


def list_received_ano_meses(
    conn: sqlite3.Connection, source_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ano_mes FROM income_months
         WHERE income_source_id = ? AND status = 'recebido'
        """,
        (source_id,),
    ).fetchall()


def list_all_join_account(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, a.nome AS conta_nome
          FROM income_sources i
          LEFT JOIN accounts a ON a.id = i.account_id
         ORDER BY CASE WHEN i.ativo = 1 THEN 0 ELSE 1 END,
                  i.nome COLLATE NOCASE
        """
    ).fetchall()


def get_join_account(conn: sqlite3.Connection, source_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, a.nome AS conta_nome
          FROM income_sources i
          LEFT JOIN accounts a ON a.id = i.account_id
         WHERE i.id = ?
        """,
        (source_id,),
    ).fetchone()


def sum_received_in_competencias(
    conn: sqlite3.Connection,
    source_id: int,
    competencias: tuple[str, ...],
) -> float:
    if not competencias:
        return 0.0
    ph = ",".join("?" * len(competencias))
    row = conn.execute(
        f"""
        SELECT COALESCE(SUM(COALESCE(im.valor_efetivo, i.valor_mensal)), 0) AS got
          FROM income_months im
          JOIN income_sources i ON i.id = im.income_source_id
         WHERE im.income_source_id = ?
           AND im.ano_mes IN ({ph})
           AND im.status = 'recebido'
        """,
        (source_id, *competencias),
    ).fetchone()
    return float(row["got"] or 0)


def sum_renda_ledger_month(conn: sqlite3.Connection, ano_mes: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS t
          FROM account_transactions
         WHERE origem = 'renda'
           AND substr(data, 1, 7) = ?
        """,
        (ano_mes,),
    ).fetchone()
    return float(row["t"] or 0)


def list_renda_ledger_rows(
    conn: sqlite3.Connection, limit: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT at.data, at.valor, at.descricao, a.nome AS conta
          FROM account_transactions at
          JOIN accounts a ON a.id = at.account_id
         WHERE at.origem = 'renda'
         ORDER BY date(at.data) DESC, at.id DESC
         LIMIT ?
        """,
        (limit,),
    ).fetchall()


def insert_source(
    conn: sqlite3.Connection,
    *,
    nome: str,
    valor_mensal: float,
    ativo: int,
    dia_recebimento: int,
    account_id: Optional[int],
    observacao: Optional[str],
    tipo: str,
    mes_referencia: Optional[str],
    total_parcelas: Optional[int],
    parcelas_tp: int,
    forma_recebimento: Optional[str],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO income_sources (
            nome, valor_mensal, ativo, dia_recebimento, account_id, observacao,
            tipo, mes_referencia, total_parcelas, parcelas_recebidas, forma_recebimento
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            valor_mensal,
            ativo,
            dia_recebimento,
            account_id,
            observacao,
            tipo,
            mes_referencia,
            total_parcelas,
            parcelas_tp,
            forma_recebimento,
        ),
    )
    return int(cur.lastrowid)


def update_source(
    conn: sqlite3.Connection,
    *,
    source_id: int,
    nome: str,
    valor_mensal: float,
    ativo: int,
    dia_recebimento: int,
    account_id: Optional[int],
    observacao: Optional[str],
    tipo: str,
    mes_referencia: Optional[str],
    total_parcelas: Optional[int],
    parcelas_tp: int,
    forma_recebimento: Optional[str],
) -> None:
    conn.execute(
        """
        UPDATE income_sources
           SET nome = ?, valor_mensal = ?, ativo = ?, dia_recebimento = ?,
               account_id = ?, observacao = ?, tipo = ?, mes_referencia = ?,
               total_parcelas = ?, parcelas_recebidas = ?, forma_recebimento = ?
         WHERE id = ?
        """,
        (
            nome,
            valor_mensal,
            ativo,
            dia_recebimento,
            account_id,
            observacao,
            tipo,
            mes_referencia,
            total_parcelas,
            parcelas_tp,
            forma_recebimento,
            source_id,
        ),
    )


def delete_by_id(conn: sqlite3.Connection, source_id: int) -> None:
    conn.execute("DELETE FROM income_sources WHERE id = ?", (source_id,))
