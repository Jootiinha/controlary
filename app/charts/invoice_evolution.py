"""Parcelas por mês + assinaturas em cartão (realizado e projeção estimada)."""
from __future__ import annotations

from datetime import date
from typing import Literal

from matplotlib.ticker import FuncFormatter

from app.charts.cards_window import (
    MONTHS_FUTURE,
    add_months,
    cards_window,
    months_between_inclusive,
)
from app.charts.plot_labels import annotate_line_points
from app.database.connection import transaction
from app.models.installment import Installment
from app.services import installments_service, subscriptions_service
from app.utils.formatting import format_currency_short

CartaoScope = Literal["all"] | int | None

_CARD_LINE_COLORS = (
    "#D97706",
    "#2563EB",
    "#7C3AED",
    "#DB2777",
    "#0D9488",
    "#EA580C",
    "#4F46E5",
    "#059669",
)

# Paleta partilhada com outros gráficos por cartão (ex.: invoices_history).
CARD_LINE_COLORS = _CARD_LINE_COLORS


def _installment_schedule(inst: Installment) -> list[str]:
    end = add_months(inst.mes_referencia, inst.total_parcelas - 1)
    return months_between_inclusive(inst.mes_referencia, end)


def build_realizado_map(current_ym: str, cartao_scope: CartaoScope) -> dict[str, float]:
    """Soma parcelas em cada mês do cronograma + assinaturas ativas (aprox.)."""
    wm = cards_window(current_ym)
    past_months = [m for m in wm if m <= current_ym]
    acc = {m: 0.0 for m in past_months}

    for inst in installments_service.list_all():
        if cartao_scope == "all":
            pass
        elif isinstance(cartao_scope, int):
            if inst.cartao_id != cartao_scope:
                continue
        else:
            if inst.cartao_id is not None:
                continue
        for m in _installment_schedule(inst):
            if m in acc:
                acc[m] += float(inst.valor_parcela)

    if cartao_scope == "all":
        subs = _subs_total_on_cards()
    elif isinstance(cartao_scope, int):
        subs = _subs_total_for_card(cartao_scope)
    else:
        subs = _subs_total_for_card(None)

    for m in past_months:
        acc[m] = round(acc[m] + subs, 2)
    return acc


def _card_name_map() -> dict[int, str]:
    with transaction() as conn:
        rows = conn.execute("SELECT id, nome FROM cards").fetchall()
    return {int(r["id"]): str(r["nome"]) for r in rows}


def _card_ids_for_chart() -> list[int | None]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT cartao_id AS cid FROM installments
             WHERE cartao_id IS NOT NULL
            UNION
            SELECT DISTINCT card_id AS cid FROM subscriptions
             WHERE status = 'ativa' AND card_id IS NOT NULL
            """
        ).fetchall()
    ids: list[int | None] = [int(r["cid"]) for r in rows]
    with transaction() as conn:
        has_null = conn.execute(
            "SELECT 1 FROM installments WHERE cartao_id IS NULL LIMIT 1"
        ).fetchone()
    if has_null:
        ids.append(None)
    ids.sort(key=lambda x: (x is None, x if x is not None else -1))
    return ids


def _subs_total_for_card(card_id: int | None) -> float:
    return round(
        sum(
            float(s.valor_mensal)
            for s in subscriptions_service.list_all()
            if s.status == "ativa"
            and (s.card_id == card_id if card_id is not None else s.card_id is None)
        ),
        2,
    )


def _subs_total_on_cards() -> float:
    return round(
        sum(
            float(s.valor_mensal)
            for s in subscriptions_service.list_all()
            if s.status == "ativa" and s.card_id is not None
        ),
        2,
    )


def fetch_realizado_one_card(
    current_ym: str, cartao_id: int | None
) -> tuple[list[str], list[float]]:
    d = build_realizado_map(current_ym, cartao_id)
    meses = sorted(d.keys())
    return meses, [d[m] for m in meses]


def fetch_projecao_one_card(
    current_ym: str, cartao_id: int | None
) -> tuple[list[str], list[float]]:
    window_end = add_months(current_ym, MONTHS_FUTURE)
    insts = [
        i
        for i in installments_service.list_all()
        if i.status == "ativo"
        and i.parcelas_restantes > 0
        and (i.cartao_id == cartao_id if cartao_id is not None else i.cartao_id is None)
    ]
    parcel_by_month: dict[str, float] = {}
    for inst in insts:
        start = inst.mes_referencia
        rem = inst.parcelas_restantes
        end = add_months(start, rem - 1)
        for m in months_between_inclusive(start, end):
            parcel_by_month[m] = parcel_by_month.get(m, 0.0) + float(inst.valor_parcela)

    subs = _subs_total_for_card(cartao_id)

    if not insts:
        if subs <= 0:
            return [], []
        meses = months_between_inclusive(current_ym, window_end)
        valores = [round(subs, 2)] * len(meses)
        return meses, valores

    last_proj = max(
        add_months(i.mes_referencia, i.parcelas_restantes - 1) for i in insts
    )
    last_proj = min(last_proj, window_end)

    if last_proj < current_ym:
        return [], []

    meses = months_between_inclusive(current_ym, last_proj)
    valores = [round(parcel_by_month.get(m, 0.0) + subs, 2) for m in meses]
    return meses, valores


def fetch_realizado(current_ym: str) -> tuple[list[str], list[float]]:
    d = build_realizado_map(current_ym, "all")
    meses = sorted(d.keys())
    return meses, [d[m] for m in meses]


def fetch_projecao(current_ym: str) -> tuple[list[str], list[float]]:
    window_end = add_months(current_ym, MONTHS_FUTURE)
    insts = [
        i
        for i in installments_service.list_all()
        if i.status == "ativo" and i.parcelas_restantes > 0
    ]
    parcel_by_month: dict[str, float] = {}
    for inst in insts:
        start = inst.mes_referencia
        rem = inst.parcelas_restantes
        end = add_months(start, rem - 1)
        for m in months_between_inclusive(start, end):
            parcel_by_month[m] = parcel_by_month.get(m, 0.0) + float(inst.valor_parcela)

    subs = _subs_total_on_cards()

    if not insts:
        if subs <= 0:
            return [], []
        meses = months_between_inclusive(current_ym, window_end)
        valores = [round(subs, 2)] * len(meses)
        return meses, valores

    last_proj = max(
        add_months(i.mes_referencia, i.parcelas_restantes - 1) for i in insts
    )
    last_proj = min(last_proj, window_end)

    if last_proj < current_ym:
        return [], []

    meses = months_between_inclusive(current_ym, last_proj)
    valores = [
        round(parcel_by_month.get(m, 0.0) + subs, 2) for m in meses
    ]
    return meses, valores


def _value_at(meses: list[str], vals: list[float], ym: str) -> float:
    if ym in meses:
        return vals[meses.index(ym)]
    return 0.0


def plot(ax) -> None:
    today = date.today()
    current_ym = f"{today.year:04d}-{today.month:02d}"

    meses_r, valores_r = fetch_realizado(current_ym)
    meses_p, valores_p = fetch_projecao(current_ym)

    if not meses_r and not meses_p:
        ax.text(
            0.5,
            0.5,
            "Sem dados de parcelamentos ou assinaturas no período",
            ha="center",
            va="center",
        )
        ax.set_axis_off()
        return

    if not meses_r and meses_p:
        meses_r = [current_ym]
        valores_r = [0.0]

    color = "#F59E0B"
    ax.plot(
        meses_r,
        valores_r,
        marker="o",
        color=color,
        linewidth=2,
        zorder=3,
        label="Realizado",
    )
    ax.fill_between(meses_r, valores_r, alpha=0.15, color=color, zorder=1)
    annotate_line_points(ax, meses_r, valores_r, fontsize=7, dy=7)

    if meses_p and valores_p:
        yv_cur = _value_at(meses_r, valores_r, current_ym)
        valores_e = list(valores_p)
        valores_e[0] = yv_cur
        ax.plot(
            meses_p,
            valores_e,
            marker="o",
            color=color,
            linewidth=2,
            linestyle="--",
            alpha=0.7,
            zorder=3,
            label="Estimado",
        )
        if len(meses_p) > 1:
            annotate_line_points(
                ax, meses_p[1:], valores_e[1:], fontsize=7, dy=7, clip_on=True
            )

    if current_ym in cards_window(current_ym):
        ax.axvline(current_ym, color="#9CA3AF", linewidth=0.9, linestyle=":")

    leg = ax.legend(loc="best", fontsize=8, framealpha=0.95, edgecolor="#E5E7EB")
    if leg is not None:
        leg.get_frame().set_linewidth(0.8)

    ax.set_title(
        "Parcelas + assinaturas recorrentes (6 passados · 12 futuros)",
        fontsize=9,
        pad=8,
    )
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")


def plot_by_card(ax) -> None:
    today = date.today()
    current_ym = f"{today.year:04d}-{today.month:02d}"

    card_ids = _card_ids_for_chart()
    if not card_ids:
        ax.text(
            0.5,
            0.5,
            "Nenhum cartão com parcelamento ou assinatura no cartão",
            ha="center",
            va="center",
        )
        ax.set_axis_off()
        return

    names = _card_name_map()
    any_line = False

    for idx, cid in enumerate(card_ids):
        meses_r, valores_r = fetch_realizado_one_card(current_ym, cid)
        meses_p, valores_p = fetch_projecao_one_card(current_ym, cid)
        if not meses_r and not meses_p:
            continue

        any_line = True
        label = names.get(cid, f"Cartão #{cid}") if cid is not None else "Sem cartão"
        color = _CARD_LINE_COLORS[idx % len(_CARD_LINE_COLORS)]

        if not meses_r and meses_p:
            meses_r = [current_ym]
            valores_r = [0.0]

        ax.plot(
            meses_r,
            valores_r,
            marker="o",
            color=color,
            linewidth=2,
            label=label,
            zorder=3,
        )

        if meses_p and valores_p:
            yv_cur = _value_at(meses_r, valores_r, current_ym)
            valores_e = list(valores_p)
            valores_e[0] = yv_cur
            ax.plot(
                meses_p,
                valores_e,
                marker="o",
                color=color,
                linewidth=2,
                linestyle="--",
                alpha=0.65,
                zorder=2,
            )

    if not any_line:
        ax.text(
            0.5,
            0.5,
            "Sem dados no período",
            ha="center",
            va="center",
        )
        ax.set_axis_off()
        return

    wm = cards_window(current_ym)
    if wm and current_ym in wm:
        ax.axvline(current_ym, color="#9CA3AF", linewidth=0.9, linestyle=":")

    leg = ax.legend(loc="best", fontsize=7, framealpha=0.95, edgecolor="#E5E7EB", ncol=2)
    if leg is not None:
        leg.get_frame().set_linewidth(0.8)

    ax.set_title(
        "Parcelas + assinaturas por cartão (6 passados · 12 futuros)",
        fontsize=9,
        pad=8,
    )
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: format_currency_short(v))
    )
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.grid(True, axis="y", alpha=0.22)
