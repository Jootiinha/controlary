"""CRUD e agregações para fontes de renda (recorrente, avulsa e parcelada)."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from app.database.connection import transaction
from app.models.income_source import IncomeSource, competencias_parcelada
from app.services import accounts_service, income_months_service


def applies_to_month(src: IncomeSource, mes: str) -> bool:
    if not src.ativo:
        return False
    if src.tipo == "recorrente":
        return True
    if src.tipo == "avulsa":
        return bool(src.mes_referencia and src.mes_referencia == mes)
    if src.tipo == "parcelada":
        if not src.mes_referencia or not src.total_parcelas:
            return False
        return mes in competencias_parcelada(src.mes_referencia, src.total_parcelas)
    return False


def _valid_month_keys_for_prune(src: IncomeSource) -> Optional[set[str]]:
    if src.tipo == "recorrente":
        return None
    if src.tipo == "avulsa" and src.mes_referencia:
        return {src.mes_referencia}
    if src.tipo == "parcelada" and src.mes_referencia and src.total_parcelas:
        return set(competencias_parcelada(src.mes_referencia, src.total_parcelas))
    return None


def _validate(src: IncomeSource) -> None:
    if src.tipo not in ("recorrente", "avulsa", "parcelada"):
        raise ValueError("Tipo de renda inválido")
    if src.tipo != "recorrente" and not src.mes_referencia:
        raise ValueError("Mês de referência é obrigatório")
    if src.tipo == "parcelada":
        if src.total_parcelas is None or src.total_parcelas < 1:
            raise ValueError("Total de parcelas inválido")
        if src.parcelas_recebidas < 0 or src.parcelas_recebidas > src.total_parcelas:
            raise ValueError("Parcelas recebidas fora do intervalo")
    if src.valor_mensal <= 0:
        raise ValueError("Valor deve ser maior que zero")


def _sync_parcelas_recebidas(src: IncomeSource) -> None:
    if src.id is None or src.tipo != "parcelada":
        return
    if not src.mes_referencia or not src.total_parcelas:
        return
    months = competencias_parcelada(src.mes_referencia, src.total_parcelas)
    for i, ym in enumerate(months):
        income_months_service.set_month_status(
            src.id, ym, recebido=(i < src.parcelas_recebidas)
        )


def _prune_to_match_source(source_id: int, src: IncomeSource) -> None:
    vk = _valid_month_keys_for_prune(src)
    if vk is None:
        return
    income_months_service.delete_rows_not_in(source_id, vk)


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


def paid_remaining(src: IncomeSource) -> tuple[float, float]:
    """Valor já recebido e valor restante para uma fonte avulsa/parcelada."""
    if src.id is None or src.tipo == "recorrente":
        return 0.0, 0.0
    competencias = src.competencias()
    if not competencias:
        return 0.0, 0.0
    received = income_months_service.count_received(src.id, competencias)
    total = len(competencias)
    valor = float(src.valor_mensal)
    return round(received * valor, 2), round(max(total - received, 0) * valor, 2)


def sum_for_month(mes: str) -> float:
    total = 0.0
    for src in list_all():
        if applies_to_month(src, mes):
            total += float(src.valor_mensal)
    return round(total, 2)


def sum_active_monthly() -> float:
    """Compatível com código legado: mês civil atual."""
    from app.utils.formatting import current_month

    return sum_for_month(current_month())


def sum_expected_receipts_rest_of_month(ano_mes: str) -> float:
    """Entradas ainda esperadas no mês: dia >= hoje e não marcadas como recebidas."""
    today = date.today()
    cur_mes = f"{today.year:04d}-{today.month:02d}"
    if ano_mes != cur_mes:
        return 0.0
    d0 = today.day
    total = 0.0
    for src in list_all():
        if not applies_to_month(src, ano_mes):
            continue
        if int(src.dia_recebimento or 5) < d0:
            continue
        if src.id is None:
            continue
        if income_months_service.is_received(src.id, ano_mes):
            continue
        total += float(src.valor_mensal)
    return round(total, 2)


def create(src: IncomeSource) -> int:
    _validate(src)
    tp = src.parcelas_recebidas if src.tipo == "parcelada" else 0
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO income_sources (
                nome, valor_mensal, ativo, dia_recebimento, account_id, observacao,
                tipo, mes_referencia, total_parcelas, parcelas_recebidas, forma_recebimento
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                src.nome,
                src.valor_mensal,
                1 if src.ativo else 0,
                src.dia_recebimento,
                src.account_id,
                src.observacao,
                src.tipo,
                src.mes_referencia,
                src.total_parcelas if src.tipo == "parcelada" else None,
                tp,
                src.forma_recebimento,
            ),
        )
        new_id = int(cur.lastrowid)
    created = get(new_id)
    if created is None:
        raise RuntimeError("Falha ao recarregar fonte de renda criada")
    _prune_to_match_source(new_id, created)
    if created.tipo == "parcelada" and created.parcelas_recebidas > 0:
        _sync_parcelas_recebidas(created)
    return new_id


def update(src: IncomeSource) -> None:
    if src.id is None:
        raise ValueError("Fonte de renda sem id não pode ser atualizada")
    _validate(src)
    tp = src.parcelas_recebidas if src.tipo == "parcelada" else 0
    with transaction() as conn:
        conn.execute(
            """
            UPDATE income_sources
               SET nome = ?, valor_mensal = ?, ativo = ?, dia_recebimento = ?,
                   account_id = ?, observacao = ?, tipo = ?, mes_referencia = ?,
                   total_parcelas = ?, parcelas_recebidas = ?, forma_recebimento = ?
             WHERE id = ?
            """,
            (
                src.nome,
                src.valor_mensal,
                1 if src.ativo else 0,
                src.dia_recebimento,
                src.account_id,
                src.observacao,
                src.tipo,
                src.mes_referencia,
                src.total_parcelas if src.tipo == "parcelada" else None,
                tp,
                src.forma_recebimento,
                src.id,
            ),
        )
    fresh = get(src.id)
    if fresh is None:
        return
    _prune_to_match_source(src.id, fresh)
    if fresh.tipo == "parcelada":
        _sync_parcelas_recebidas(fresh)


def delete(source_id: int) -> None:
    with transaction() as conn:
        accounts_service.remove_transaction_keys_like_prefix(
            f"income:{source_id}:", conn=conn
        )
        conn.execute("DELETE FROM income_sources WHERE id = ?", (source_id,))
