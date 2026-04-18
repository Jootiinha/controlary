"""Gráfico de evolução da fatura (parcelas por mês + projeção estimada)."""
from __future__ import annotations

from datetime import date

from app.charts.plot_labels import annotate_line_points
from app.database.connection import transaction
from app.services import installments_service, subscriptions_service


def _parse_ym(ym: str) -> tuple[int, int]:
    y, m = ym.split("-", 1)
    return int(y), int(m)


def _ym_key(y: int, m: int) -> str:
    return f"{y:04d}-{m:02d}"


def _add_months(ym: str, n: int) -> str:
    y, mo = _parse_ym(ym)
    idx = (y * 12 + mo - 1) + n
    y2 = idx // 12
    m2 = idx % 12 + 1
    return _ym_key(y2, m2)


def _months_between_inclusive(start: str, end: str) -> list[str]:
    if start > end:
        return []
    out: list[str] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur = _add_months(cur, 1)
    return out


def fetch_realizado_raw() -> dict[str, float]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT mes_referencia AS mes, SUM(valor_parcela) AS total
              FROM installments
             GROUP BY mes_referencia
             ORDER BY mes_referencia ASC
            """
        ).fetchall()
    return {r["mes"]: float(r["total"] or 0) for r in rows}


def fetch_realizado(current_ym: str) -> tuple[list[str], list[float]]:
    raw = fetch_realizado_raw()
    if not raw:
        return [], []
    first = min(raw.keys())
    if first > current_ym:
        return [], []
    meses = _months_between_inclusive(first, current_ym)
    valores = [round(raw.get(m, 0.0), 2) for m in meses]
    return meses, valores


def _subs_total_on_cards() -> float:
    return round(
        sum(
            float(s.valor_mensal)
            for s in subscriptions_service.list_all()
            if s.status == "ativa" and s.card_id is not None
        ),
        2,
    )


def fetch_projecao(current_ym: str) -> tuple[list[str], list[float]]:
    insts = [
        i
        for i in installments_service.list_all()
        if i.status == "ativo" and i.parcelas_restantes > 0
    ]
    if not insts:
        return [], []

    parcel_by_month: dict[str, float] = {}
    for inst in insts:
        start = inst.mes_referencia
        rem = inst.parcelas_restantes
        end = _add_months(start, rem - 1)
        for m in _months_between_inclusive(start, end):
            parcel_by_month[m] = parcel_by_month.get(m, 0.0) + float(inst.valor_parcela)

    last_proj = max(
        _add_months(i.mes_referencia, i.parcelas_restantes - 1) for i in insts
    )
    if last_proj < current_ym:
        return [], []

    subs = _subs_total_on_cards()
    meses = _months_between_inclusive(current_ym, last_proj)
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
        ax.text(0.5, 0.5, "Sem dados de parcelamentos", ha="center", va="center")
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

    leg = ax.legend(loc="best", fontsize=8, framealpha=0.95, edgecolor="#E5E7EB")
    if leg is not None:
        leg.get_frame().set_linewidth(0.8)

    ax.set_title("Evolução da fatura por mês de referência")
    ax.set_ylabel("R$")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
