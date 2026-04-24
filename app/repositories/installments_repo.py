"""SQL puro para installments e leituras auxiliares."""
from __future__ import annotations

import sqlite3
from typing import Optional


def list_all_joined(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, c.nome AS cartao_nome, a.nome AS account_nome, cat.nome AS categoria_nome
          FROM installments i
          LEFT JOIN cards c ON c.id = i.cartao_id
          LEFT JOIN accounts a ON a.id = i.account_id
          LEFT JOIN categories cat ON cat.id = i.category_id
         ORDER BY i.status ASC, i.id DESC
        """
    ).fetchall()


def get_joined(
    conn: sqlite3.Connection, installment_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, c.nome AS cartao_nome, a.nome AS account_nome, cat.nome AS categoria_nome
          FROM installments i
          LEFT JOIN cards c ON c.id = i.cartao_id
          LEFT JOIN accounts a ON a.id = i.account_id
          LEFT JOIN categories cat ON cat.id = i.category_id
         WHERE i.id = ?
        """,
        (installment_id,),
    ).fetchone()


def fetch_card_nome(conn: sqlite3.Connection, card_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT nome FROM cards WHERE id = ?",
        (card_id,),
    ).fetchone()


def fetch_account_nome(conn: sqlite3.Connection, account_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT nome FROM accounts WHERE id = ?",
        (account_id,),
    ).fetchone()


def insert_on_card(
    conn: sqlite3.Connection,
    *,
    nome_fatura: str,
    nome_cartao: str,
    cartao_id: int,
    mes_referencia: str,
    valor_parcela: float,
    total_parcelas: int,
    parcelas_pagas: int,
    status: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO installments (
            nome_fatura, cartao, cartao_id, account_id, mes_referencia, valor_parcela,
            total_parcelas, parcelas_pagas, status, observacao, category_id
        ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome_fatura,
            nome_cartao,
            cartao_id,
            mes_referencia,
            valor_parcela,
            total_parcelas,
            parcelas_pagas,
            status,
            observacao,
            category_id,
        ),
    )
    return int(cur.lastrowid)


def insert_on_account(
    conn: sqlite3.Connection,
    *,
    nome_fatura: str,
    cartao_label: str,
    account_id: int,
    mes_referencia: str,
    valor_parcela: float,
    total_parcelas: int,
    parcelas_pagas: int,
    status: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO installments (
            nome_fatura, cartao, cartao_id, account_id, mes_referencia, valor_parcela,
            total_parcelas, parcelas_pagas, status, observacao, category_id
        ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome_fatura,
            cartao_label,
            account_id,
            mes_referencia,
            valor_parcela,
            total_parcelas,
            parcelas_pagas,
            status,
            observacao,
            category_id,
        ),
    )
    return int(cur.lastrowid)


def update_on_card(
    conn: sqlite3.Connection,
    *,
    installment_id: int,
    nome_fatura: str,
    nome_cartao: str,
    cartao_id: int,
    mes_referencia: str,
    valor_parcela: float,
    total_parcelas: int,
    parcelas_pagas: int,
    status: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> None:
    conn.execute(
        """
        UPDATE installments
           SET nome_fatura = ?, cartao = ?, cartao_id = ?, account_id = NULL,
               mes_referencia = ?, valor_parcela = ?, total_parcelas = ?,
               parcelas_pagas = ?, status = ?, observacao = ?, category_id = ?
         WHERE id = ?
        """,
        (
            nome_fatura,
            nome_cartao,
            cartao_id,
            mes_referencia,
            valor_parcela,
            total_parcelas,
            parcelas_pagas,
            status,
            observacao,
            category_id,
            installment_id,
        ),
    )


def update_on_account(
    conn: sqlite3.Connection,
    *,
    installment_id: int,
    nome_fatura: str,
    cartao_label: str,
    account_id: int,
    mes_referencia: str,
    valor_parcela: float,
    total_parcelas: int,
    parcelas_pagas: int,
    status: str,
    observacao: Optional[str],
    category_id: Optional[int],
) -> None:
    conn.execute(
        """
        UPDATE installments
           SET nome_fatura = ?, cartao = ?, cartao_id = NULL, account_id = ?,
               mes_referencia = ?, valor_parcela = ?, total_parcelas = ?,
               parcelas_pagas = ?, status = ?, observacao = ?, category_id = ?
         WHERE id = ?
        """,
        (
            nome_fatura,
            cartao_label,
            account_id,
            mes_referencia,
            valor_parcela,
            total_parcelas,
            parcelas_pagas,
            status,
            observacao,
            category_id,
            installment_id,
        ),
    )


def list_paid_ano_meses_for_installment(
    conn: sqlite3.Connection, installment_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ano_mes FROM installment_months
         WHERE installment_id = ? AND status = 'pago'
        """,
        (installment_id,),
    ).fetchall()


def list_id_mesref_total_ativos_cartao(
    conn: sqlite3.Connection, cartao_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, mes_referencia, total_parcelas FROM installments
         WHERE status = 'ativo'
           AND cartao_id = ?
        """,
        (cartao_id,),
    ).fetchall()


def list_id_mesref_total_cartao_ativo_quitado(
    conn: sqlite3.Connection, cartao_id: int
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, mes_referencia, total_parcelas FROM installments
         WHERE cartao_id = ?
           AND status IN ('ativo', 'quitado')
        """,
        (cartao_id,),
    ).fetchall()


def fetch_parcelas_pagas_total(
    conn: sqlite3.Connection, installment_id: int
) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT parcelas_pagas, total_parcelas FROM installments WHERE id = ?",
        (installment_id,),
    ).fetchone()


def update_parcelas_pagas_status(
    conn: sqlite3.Connection,
    installment_id: int,
    parcelas_pagas: int,
    status: str,
) -> None:
    conn.execute(
        """
        UPDATE installments SET parcelas_pagas = ?, status = ? WHERE id = ?
        """,
        (parcelas_pagas, status, installment_id),
    )


def delete_by_id(conn: sqlite3.Connection, installment_id: int) -> None:
    conn.execute("DELETE FROM installments WHERE id = ?", (installment_id,))


def sum_active_debt(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(valor_parcela * (total_parcelas - parcelas_pagas)), 0) AS saldo
          FROM installments
         WHERE status = 'ativo'
        """
    ).fetchone()
    return float(row["saldo"] or 0)
