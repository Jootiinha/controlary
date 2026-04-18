"""Operações sobre parcelamentos com cálculo automático de status."""
from __future__ import annotations

from typing import List, Optional

from app.database.connection import transaction
from app.models.installment import Installment


def _compute_status(parcelas_pagas: int, total_parcelas: int) -> str:
    return "quitado" if parcelas_pagas >= total_parcelas else "ativo"


def list_all() -> List[Installment]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT i.*, c.nome AS cartao_nome
              FROM installments i
              LEFT JOIN cards c ON c.id = i.cartao_id
             ORDER BY i.status ASC, i.id DESC
            """
        ).fetchall()
    return [Installment.from_row(r) for r in rows]


def get(installment_id: int) -> Optional[Installment]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT i.*, c.nome AS cartao_nome
              FROM installments i
              LEFT JOIN cards c ON c.id = i.cartao_id
             WHERE i.id = ?
            """,
            (installment_id,),
        ).fetchone()
    return Installment.from_row(row) if row else None


def create(installment: Installment) -> int:
    if not installment.cartao_id:
        raise ValueError("Selecione um cartão")
    status = _compute_status(installment.parcelas_pagas, installment.total_parcelas)
    with transaction() as conn:
        row = conn.execute(
            "SELECT nome FROM cards WHERE id = ?", (installment.cartao_id,)
        ).fetchone()
        if not row:
            raise ValueError("Cartão inválido")
        nome_cartao = row["nome"]
        cur = conn.execute(
            """
            INSERT INTO installments (
                nome_fatura, cartao, cartao_id, mes_referencia, valor_parcela,
                total_parcelas, parcelas_pagas, status, observacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                installment.nome_fatura,
                nome_cartao,
                installment.cartao_id,
                installment.mes_referencia,
                installment.valor_parcela,
                installment.total_parcelas,
                installment.parcelas_pagas,
                status,
                installment.observacao,
            ),
        )
        return int(cur.lastrowid)


def update(installment: Installment) -> None:
    if installment.id is None:
        raise ValueError("Parcelamento sem id não pode ser atualizado")
    if not installment.cartao_id:
        raise ValueError("Selecione um cartão")
    status = _compute_status(installment.parcelas_pagas, installment.total_parcelas)
    with transaction() as conn:
        row = conn.execute(
            "SELECT nome FROM cards WHERE id = ?", (installment.cartao_id,)
        ).fetchone()
        if not row:
            raise ValueError("Cartão inválido")
        nome_cartao = row["nome"]
        conn.execute(
            """
            UPDATE installments
               SET nome_fatura = ?, cartao = ?, cartao_id = ?, mes_referencia = ?,
                   valor_parcela = ?, total_parcelas = ?, parcelas_pagas = ?,
                   status = ?, observacao = ?
             WHERE id = ?
            """,
            (
                installment.nome_fatura,
                nome_cartao,
                installment.cartao_id,
                installment.mes_referencia,
                installment.valor_parcela,
                installment.total_parcelas,
                installment.parcelas_pagas,
                status,
                installment.observacao,
                installment.id,
            ),
        )


def increment_paid(installment_id: int, delta: int = 1) -> None:
    """Incrementa (ou decrementa) parcelas_pagas respeitando limites."""
    inst = get(installment_id)
    if inst is None:
        raise ValueError(f"Parcelamento {installment_id} não encontrado")
    novo = max(0, min(inst.total_parcelas, inst.parcelas_pagas + delta))
    inst.parcelas_pagas = novo
    update(inst)


def delete(installment_id: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM installments WHERE id = ?", (installment_id,))


def total_debt() -> float:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(valor_parcela * (total_parcelas - parcelas_pagas)), 0) AS saldo
              FROM installments
             WHERE status = 'ativo'
            """
        ).fetchone()
    return float(row["saldo"] or 0)
