"""CRUD e agregações para fontes de renda (recorrente, avulsa e parcelada)."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import List, Optional

from app.database.connection import use
from app.events import app_events
from app.models.income_source import IncomeSource, competencias_parcelada
from app.repositories import income_sources_repo
from app.services import accounts_service, income_months_service


class DestructiveIncomeUpdateError(ValueError):
    """Alteração removeria competências já recebidas ou exige limpar histórico mensal; confirmar na UI."""


class DuplicateAvulsaIncomeError(ValueError):
    """Já existe renda avulsa com o mesmo nome no mesmo mês de competência."""


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


def _income_month_row_count(
    source_id: int, conn: Optional[sqlite3.Connection] = None
) -> int:
    with use(conn) as c:
        return income_sources_repo.count_month_rows(c, source_id)


def _received_months_outside_keep(
    source_id: int, keep: set[str], conn: Optional[sqlite3.Connection] = None
) -> list[str]:
    with use(conn) as c:
        rows = income_sources_repo.list_received_ano_meses(c, source_id)
    return [str(r["ano_mes"]) for r in rows if str(r["ano_mes"]) not in keep]


def list_all(conn: Optional[sqlite3.Connection] = None) -> List[IncomeSource]:
    with use(conn) as c:
        rows = income_sources_repo.list_all_join_account(c)
    return [IncomeSource.from_row(r) for r in rows]


def get(
    source_id: int, conn: Optional[sqlite3.Connection] = None
) -> Optional[IncomeSource]:
    with use(conn) as c:
        row = income_sources_repo.get_join_account(c, source_id)
    return IncomeSource.from_row(row) if row else None


def paid_remaining(
    src: IncomeSource,
    *,
    include_inactive: bool = True,
    conn: Optional[sqlite3.Connection] = None,
) -> tuple[float, float]:
    """Valor já recebido e valor restante para uma fonte avulsa/parcelada."""
    if src.id is None or src.tipo == "recorrente":
        return 0.0, 0.0
    if not include_inactive and not src.ativo:
        return 0.0, 0.0
    competencias = src.competencias()
    if not competencias:
        return 0.0, 0.0
    competencias_t = tuple(str(x) for x in competencias)
    with use(conn) as c:
        received_sum = income_sources_repo.sum_received_in_competencias(
            c, int(src.id), competencias_t
        )
    total_expected = float(src.valor_mensal) * len(competencias)
    remaining = max(total_expected - received_sum, 0.0)
    return round(received_sum, 2), round(remaining, 2)


def is_fully_received(src: IncomeSource) -> bool:
    """Avulsa ou parcelada com o total esperado já creditado em income_months."""
    if src.tipo not in ("avulsa", "parcelada"):
        return False
    if not src.competencias():
        return False
    _, rem = paid_remaining(src, include_inactive=True)
    return rem <= 0.0


def sum_received_for_month(
    ano_mes: str, conn: Optional[sqlite3.Connection] = None
) -> float:
    """Créditos de renda no livro-caixa no mês (origem = renda)."""
    with use(conn) as c:
        t = income_sources_repo.sum_renda_ledger_month(c, ano_mes)
    return round(t, 2)


def list_renda_ledger_rows(
    limit: int = 400, conn: Optional[sqlite3.Connection] = None
) -> list[tuple[str, float, str, str]]:
    """Linhas para histórico: (data ISO, valor, descrição, conta)."""
    with use(conn) as c:
        rows = income_sources_repo.list_renda_ledger_rows(c, limit)
    out: list[tuple[str, float, str, str]] = []
    for r in rows:
        out.append(
            (
                str(r["data"]),
                float(r["valor"] or 0),
                (r["descricao"] or "").strip(),
                str(r["conta"] or ""),
            )
        )
    return out


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
    """Entradas esperadas no mês civil corrente ainda não marcadas como recebidas (competência)."""
    today = date.today()
    cur_mes = f"{today.year:04d}-{today.month:02d}"
    if ano_mes != cur_mes:
        return 0.0
    total = 0.0
    for src in list_all():
        if not applies_to_month(src, ano_mes):
            continue
        if src.id is None:
            continue
        if income_months_service.is_received(src.id, ano_mes):
            continue
        total += float(src.valor_mensal)
    return round(total, 2)


def create(
    src: IncomeSource,
    *,
    allow_duplicate_avulsa: bool = False,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    _validate(src)
    tp = src.parcelas_recebidas if src.tipo == "parcelada" else 0
    with use(conn) as c:
        if (
            src.tipo == "avulsa"
            and src.mes_referencia
            and not allow_duplicate_avulsa
            and income_sources_repo.avulsa_duplicate(
                c, src.nome, src.mes_referencia, None
            )
        ):
            raise DuplicateAvulsaIncomeError(
                "Já existe outra renda avulsa com o mesmo nome neste mês de competência."
            )
        new_id = income_sources_repo.insert_source(
            c,
            nome=src.nome.strip(),
            valor_mensal=float(src.valor_mensal),
            ativo=1 if src.ativo else 0,
            dia_recebimento=int(src.dia_recebimento),
            account_id=src.account_id,
            observacao=src.observacao,
            tipo=src.tipo,
            mes_referencia=src.mes_referencia,
            total_parcelas=src.total_parcelas if src.tipo == "parcelada" else None,
            parcelas_tp=tp,
            forma_recebimento=src.forma_recebimento,
        )
        row = income_sources_repo.get_join_account(c, new_id)
    created = IncomeSource.from_row(row) if row else None
    if created is None:
        raise RuntimeError("Falha ao recarregar fonte de renda criada")
    _prune_to_match_source(new_id, created)
    if created.tipo == "parcelada" and created.parcelas_recebidas > 0:
        _sync_parcelas_recebidas(created)
    app_events().income_changed.emit()
    return new_id


def update(
    src: IncomeSource,
    *,
    confirm_destructive_prune: bool = False,
    allow_duplicate_avulsa: bool = False,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    if src.id is None:
        raise ValueError("Fonte de renda sem id não pode ser atualizada")
    before = get(src.id, conn=conn)
    if before is None:
        raise ValueError("Fonte de renda não encontrada")
    _validate(src)
    tp = src.parcelas_recebidas if src.tipo == "parcelada" else 0

    if src.tipo == "avulsa" and src.mes_referencia and not allow_duplicate_avulsa:
        with use(conn) as c:
            if income_sources_repo.avulsa_duplicate(
                c, src.nome, src.mes_referencia, src.id
            ):
                raise DuplicateAvulsaIncomeError(
                    "Já existe outra renda avulsa com o mesmo nome neste mês de competência."
                )

    if src.tipo == "recorrente" and before.tipo != "recorrente":
        if _income_month_row_count(src.id, conn=conn) > 0 and not confirm_destructive_prune:
            raise DestructiveIncomeUpdateError(
                "Tornar esta fonte recorrente remove o histórico de competências mensais "
                "(incluindo recebimentos e lançamentos no livro-caixa associados a esses meses)."
            )

    vk_new = _valid_month_keys_for_prune(src)
    if vk_new is not None and not confirm_destructive_prune:
        lost = _received_months_outside_keep(src.id, vk_new, conn=conn)
        if lost:
            raise DestructiveIncomeUpdateError(
                "A alteração removeria competências já recebidas no livro-caixa: "
                + ", ".join(sorted(lost))
                + "."
            )

    with use(conn) as c:
        income_sources_repo.update_source(
            c,
            source_id=int(src.id),
            nome=src.nome.strip(),
            valor_mensal=float(src.valor_mensal),
            ativo=1 if src.ativo else 0,
            dia_recebimento=int(src.dia_recebimento),
            account_id=src.account_id,
            observacao=src.observacao,
            tipo=src.tipo,
            mes_referencia=src.mes_referencia,
            total_parcelas=src.total_parcelas if src.tipo == "parcelada" else None,
            parcelas_tp=tp,
            forma_recebimento=src.forma_recebimento,
        )
    fresh = get(src.id, conn=conn)
    if fresh is None:
        return
    if (
        fresh.tipo == "recorrente"
        and before.tipo != "recorrente"
        and confirm_destructive_prune
    ):
        income_months_service.delete_rows_not_in(src.id, set())
    _prune_to_match_source(src.id, fresh)
    if fresh.tipo == "parcelada":
        _sync_parcelas_recebidas(fresh)
    app_events().income_changed.emit()


def delete(source_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    with use(conn) as c:
        accounts_service.remove_transaction_keys_like_prefix(
            f"income:{source_id}:", conn=c
        )
        income_sources_repo.delete_by_id(c, source_id)
    app_events().income_changed.emit()
