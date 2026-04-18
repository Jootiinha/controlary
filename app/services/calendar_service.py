"""Agrega lançamentos e compromissos por data para o calendário e próximos vencimentos."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from app.services import (
    card_invoices_service,
    cards_service,
    fixed_expenses_service,
    income_sources_service,
    installments_service,
    payments_service,
    subscriptions_service,
)
from app.utils.formatting import parse_date

CalendarEventType = Literal[
    "pagamento", "renda", "assinatura", "fixo", "parcela", "fatura"
]

PARCELA_FALLBACK_DIA = 1

UPCOMING_HORIZON_DAYS = 14

_TIPO_ORDEM: dict[CalendarEventType, int] = {
    "renda": 0,
    "pagamento": 1,
    "fatura": 2,
    "assinatura": 3,
    "fixo": 4,
    "parcela": 5,
}


@dataclass(frozen=True)
class CalendarEvent:
    data: date
    titulo: str
    valor: float
    tipo: CalendarEventType
    ref_id: int | None = None
    pago: bool = False


def _ultimo_dia_mes(ano: int, mes: int) -> int:
    return calendar.monthrange(ano, mes)[1]


def _data_com_dia(ano: int, mes: int, dia: int) -> date:
    ultimo = _ultimo_dia_mes(ano, mes)
    return date(ano, mes, min(dia, ultimo))


def _months_from_until(d0: date, d1: date):
    y, m = d0.year, d0.month
    end_key = (d1.year, d1.month)
    while (y, m) <= end_key:
        yield y, m
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def _cards_with_activity_in_month(ano_mes: str, ano: int, mes: int) -> set[int]:
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, _ultimo_dia_mes(ano, mes))
    out: set[int] = set()
    for inst in installments_service.list_all():
        if inst.status != "ativo" or inst.parcelas_restantes <= 0:
            continue
        if inst.mes_referencia != ano_mes or inst.cartao_id is None:
            continue
        out.add(inst.cartao_id)
    for s in subscriptions_service.list_all():
        if s.status != "ativa" or s.card_id is None:
            continue
        out.add(s.card_id)
    for p in payments_service.list_between(primeiro, ultimo):
        if p.cartao_id is not None:
            out.add(p.cartao_id)
    return out


def events_for_month(ano: int, mes: int) -> list[CalendarEvent]:
    if not (1 <= mes <= 12):
        raise ValueError("Mês inválido")
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, _ultimo_dia_mes(ano, mes))
    ano_mes = f"{ano:04d}-{mes:02d}"

    out: list[CalendarEvent] = []

    for p in payments_service.list_between(primeiro, ultimo):
        if p.cartao_id is not None:
            continue
        d = parse_date(p.data)
        titulo = p.descricao
        if p.conta_nome:
            titulo = f"{p.descricao} ({p.conta_nome})"
        out.append(
            CalendarEvent(
                data=d,
                titulo=titulo,
                valor=float(p.valor),
                tipo="pagamento",
                ref_id=p.id,
                pago=False,
            )
        )

    for src in income_sources_service.list_all():
        if not src.ativo:
            continue
        if src.id is None:
            continue
        d = _data_com_dia(ano, mes, src.dia_recebimento)
        out.append(
            CalendarEvent(
                data=d,
                titulo=src.nome,
                valor=float(src.valor_mensal),
                tipo="renda",
                ref_id=src.id,
                pago=False,
            )
        )

    for s in subscriptions_service.list_all():
        if s.status != "ativa":
            continue
        if s.card_id is not None:
            continue
        d = _data_com_dia(ano, mes, s.dia_cobranca)
        out.append(
            CalendarEvent(
                data=d,
                titulo=s.nome,
                valor=float(s.valor_mensal),
                tipo="assinatura",
                ref_id=s.id,
                pago=False,
            )
        )

    for fe in fixed_expenses_service.list_active():
        if fe.id is None:
            continue
        d = _data_com_dia(ano, mes, fe.dia_referencia)
        st = "pago" if fixed_expenses_service.is_paid(fe.id, ano_mes) else "pendente"
        pago = st == "pago"
        out.append(
            CalendarEvent(
                data=d,
                titulo=f"{fe.nome} ({st})",
                valor=float(fe.valor_mensal),
                tipo="fixo",
                ref_id=fe.id,
                pago=pago,
            )
        )

    card_cache: dict[int, object] = {}

    def _get_card(cid: int | None):
        if cid is None:
            return None
        if cid not in card_cache:
            card_cache[cid] = cards_service.get(cid)
        return card_cache[cid]

    for inst in installments_service.list_all():
        if inst.status != "ativo" or inst.parcelas_restantes <= 0:
            continue
        if inst.mes_referencia != ano_mes:
            continue
        if inst.cartao_id is not None:
            continue
        d = date(ano, mes, PARCELA_FALLBACK_DIA)
        titulo = f"{inst.nome_fatura} — parcela"
        out.append(
            CalendarEvent(
                data=d,
                titulo=titulo,
                valor=float(inst.valor_parcela),
                tipo="parcela",
                ref_id=inst.id,
                pago=False,
            )
        )

    for cid in _cards_with_activity_in_month(ano_mes, ano, mes):
        c = _get_card(cid)
        if c is None:
            continue
        inv = card_invoices_service.get(cid, ano_mes)
        sug = card_invoices_service.suggested_total(cid, ano_mes)
        if inv is not None:
            valor = float(inv.valor_total) if inv.valor_total > 0 else sug
            pago = inv.status == "paga"
            st = inv.status
        else:
            valor = sug
            pago = False
            st = "aberta"
        if sug <= 0 and (inv is None or inv.valor_total <= 0):
            continue
        d = _data_com_dia(ano, mes, c.dia_pagamento_fatura)
        titulo = f"Fatura — {c.nome} ({st})"
        iid = inv.id if inv else None
        out.append(
            CalendarEvent(
                data=d,
                titulo=titulo,
                valor=valor,
                tipo="fatura",
                ref_id=iid,
                pago=pago,
            )
        )

    out.sort(
        key=lambda e: (e.data, _TIPO_ORDEM[e.tipo], e.titulo.casefold())
    )
    return out


def events_by_date(ano: int, mes: int) -> dict[date, list[CalendarEvent]]:
    grouped: dict[date, list[CalendarEvent]] = {}
    for ev in events_for_month(ano, mes):
        grouped.setdefault(ev.data, []).append(ev)
    return grouped


def upcoming_payables(horizon_days: int = UPCOMING_HORIZON_DAYS) -> list[CalendarEvent]:
    today = date.today()
    end = today + timedelta(days=horizon_days)
    out: list[CalendarEvent] = []
    for y, m in _months_from_until(today, end):
        for ev in events_for_month(y, m):
            if ev.tipo not in ("assinatura", "fixo", "parcela", "fatura"):
                continue
            if ev.data < today or ev.data > end:
                continue
            if ev.pago:
                continue
            if ev.tipo == "fixo" and ev.ref_id is not None:
                ano_mes = f"{ev.data.year:04d}-{ev.data.month:02d}"
                if fixed_expenses_service.is_paid(ev.ref_id, ano_mes):
                    continue
            out.append(ev)
    out.sort(
        key=lambda e: (e.data, _TIPO_ORDEM[e.tipo], e.titulo.casefold())
    )
    return out
