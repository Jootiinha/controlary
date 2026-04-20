"""Operações sobre parcelamentos com cálculo automático de status."""
from __future__ import annotations

from sqlite3 import Connection
from typing import List, Optional

from app.database.connection import transaction
from app.models.installment import Installment
from app.services import accounts_service


def _compute_status(parcelas_pagas: int, total_parcelas: int) -> str:
    return "quitado" if parcelas_pagas >= total_parcelas else "ativo"


def preview_parcelamento(
    valor_parcela: float, total_parcelas: int, parcelas_pagas: int
) -> tuple[float, int, float, str]:
    """Resumo para UI: (valor total contrato, parcelas restantes, saldo devedor, status)."""
    tot = max(int(total_parcelas), 0)
    pp = min(max(int(parcelas_pagas), 0), tot)
    restantes = tot - pp
    valor_total = round(float(valor_parcela) * tot, 2)
    saldo = round(float(valor_parcela) * restantes, 2)
    status = "quitado" if tot > 0 and pp >= tot else "ativo"
    return valor_total, restantes, saldo, status


def list_all() -> List[Installment]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT i.*, c.nome AS cartao_nome, a.nome AS account_nome, cat.nome AS categoria_nome
              FROM installments i
              LEFT JOIN cards c ON c.id = i.cartao_id
              LEFT JOIN accounts a ON a.id = i.account_id
              LEFT JOIN categories cat ON cat.id = i.category_id
             ORDER BY i.status ASC, i.id DESC
            """
        ).fetchall()
    return [Installment.from_row(r) for r in rows]


def get(installment_id: int) -> Optional[Installment]:
    with transaction() as conn:
        row = conn.execute(
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
    return Installment.from_row(row) if row else None


def create(installment: Installment) -> int:
    has_card = installment.cartao_id is not None
    has_acc = installment.account_id is not None
    if has_card == has_acc:
        raise ValueError("Informe cartão ou conta corrente (apenas um)")
    status = _compute_status(installment.parcelas_pagas, installment.total_parcelas)
    with transaction() as conn:
        if has_card:
            row = conn.execute(
                "SELECT nome FROM cards WHERE id = ?", (installment.cartao_id,)
            ).fetchone()
            if not row:
                raise ValueError("Cartão inválido")
            nome_ref = row["nome"]
            cur = conn.execute(
                """
                INSERT INTO installments (
                    nome_fatura, cartao, cartao_id, account_id, mes_referencia, valor_parcela,
                    total_parcelas, parcelas_pagas, status, observacao, category_id
                ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    installment.nome_fatura,
                    nome_ref,
                    installment.cartao_id,
                    installment.mes_referencia,
                    installment.valor_parcela,
                    installment.total_parcelas,
                    installment.parcelas_pagas,
                    status,
                    installment.observacao,
                    installment.category_id,
                ),
            )
            return int(cur.lastrowid)
        row = conn.execute(
            "SELECT nome FROM accounts WHERE id = ?", (installment.account_id,)
        ).fetchone()
        if not row:
            raise ValueError("Conta inválida")
        nome_ref = f"Conta · {row['nome']}"
        cur = conn.execute(
            """
            INSERT INTO installments (
                nome_fatura, cartao, cartao_id, account_id, mes_referencia, valor_parcela,
                total_parcelas, parcelas_pagas, status, observacao, category_id
            ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                installment.nome_fatura,
                nome_ref,
                installment.account_id,
                installment.mes_referencia,
                installment.valor_parcela,
                installment.total_parcelas,
                installment.parcelas_pagas,
                status,
                installment.observacao,
                installment.category_id,
            ),
        )
        return int(cur.lastrowid)


def update(installment: Installment) -> None:
    if installment.id is None:
        raise ValueError("Parcelamento sem id não pode ser atualizado")
    has_card = installment.cartao_id is not None
    has_acc = installment.account_id is not None
    if has_card == has_acc:
        raise ValueError("Informe cartão ou conta corrente (apenas um)")
    status = _compute_status(installment.parcelas_pagas, installment.total_parcelas)
    with transaction() as conn:
        if has_card:
            row = conn.execute(
                "SELECT nome FROM cards WHERE id = ?", (installment.cartao_id,)
            ).fetchone()
            if not row:
                raise ValueError("Cartão inválido")
            nome_ref = row["nome"]
            conn.execute(
                """
                UPDATE installments
                   SET nome_fatura = ?, cartao = ?, cartao_id = ?, account_id = NULL,
                       mes_referencia = ?, valor_parcela = ?, total_parcelas = ?,
                       parcelas_pagas = ?, status = ?, observacao = ?, category_id = ?
                 WHERE id = ?
                """,
                (
                    installment.nome_fatura,
                    nome_ref,
                    installment.cartao_id,
                    installment.mes_referencia,
                    installment.valor_parcela,
                    installment.total_parcelas,
                    installment.parcelas_pagas,
                    status,
                    installment.observacao,
                    installment.category_id,
                    installment.id,
                ),
            )
            return
        row = conn.execute(
            "SELECT nome FROM accounts WHERE id = ?", (installment.account_id,)
        ).fetchone()
        if not row:
            raise ValueError("Conta inválida")
        nome_ref = f"Conta · {row['nome']}"
        conn.execute(
            """
            UPDATE installments
               SET nome_fatura = ?, cartao = ?, cartao_id = NULL, account_id = ?,
                   mes_referencia = ?, valor_parcela = ?, total_parcelas = ?,
                   parcelas_pagas = ?, status = ?, observacao = ?, category_id = ?
             WHERE id = ?
            """,
            (
                installment.nome_fatura,
                nome_ref,
                installment.account_id,
                installment.mes_referencia,
                installment.valor_parcela,
                installment.total_parcelas,
                installment.parcelas_pagas,
                status,
                installment.observacao,
                installment.category_id,
                installment.id,
            ),
        )


def list_active_ids_for_card_month(cartao_id: int, ano_mes: str) -> list[int]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT id FROM installments
             WHERE status = 'ativo'
               AND cartao_id = ?
               AND mes_referencia = ?
            """,
            (cartao_id, ano_mes),
        ).fetchall()
    return [int(r["id"]) for r in rows]


def increment_paid_in_connection(
    conn: Connection, installment_id: int, delta: int = 1
) -> None:
    """Atualiza parcelas_pagas/status na mesma conexão (ex.: dentro de transação maior)."""
    row = conn.execute(
        "SELECT parcelas_pagas, total_parcelas FROM installments WHERE id = ?",
        (installment_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"Parcelamento {installment_id} não encontrado")
    tot = int(row["total_parcelas"] or 0)
    pp = int(row["parcelas_pagas"] or 0)
    novo = max(0, min(tot, pp + delta))
    status = _compute_status(novo, tot)
    conn.execute(
        """
        UPDATE installments SET parcelas_pagas = ?, status = ? WHERE id = ?
        """,
        (novo, status, installment_id),
    )


def increment_paid(installment_id: int, delta: int = 1) -> None:
    """Incrementa (ou decrementa) parcelas_pagas respeitando limites."""
    with transaction() as conn:
        increment_paid_in_connection(conn, installment_id, delta)


def delete(installment_id: int) -> None:
    with transaction() as conn:
        accounts_service.remove_transaction_keys_like_prefix(
            f"installment:{installment_id}:", conn=conn
        )
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
