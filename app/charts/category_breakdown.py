"""Gráfico de distribuição: assinaturas por categoria + total de gastos avulsos.

Não mistura forma de pagamento (Pix, crédito etc.) com categoria de assinatura.
"""
from __future__ import annotations

from app.database.connection import transaction
from app.utils.formatting import format_currency


def fetch_data() -> list[tuple[str, float]]:
    """Retorna (rótulo, valor) ordenado por valor decrescente."""
    with transaction() as conn:
        total_payments = conn.execute(
            "SELECT COALESCE(SUM(valor), 0) AS t FROM payments"
        ).fetchone()
        pay = float(total_payments["t"] or 0)

        rows_sub = conn.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(categoria), ''), 'Assinaturas sem categoria') AS cat,
                   SUM(valor_mensal) AS total
              FROM subscriptions
             WHERE status = 'ativa'
             GROUP BY cat
            """
        ).fetchall()

    items: list[tuple[str, float]] = []
    for r in rows_sub:
        total = float(r["total"] or 0)
        if total > 0:
            items.append((r["cat"], total))

    if pay > 0:
        items.append(("Demais gastos (lançamentos avulsos)", pay))

    items.sort(key=lambda x: x[1], reverse=True)
    return items


def plot(ax) -> None:
    data = fetch_data()
    if not data:
        ax.text(0.5, 0.5, "Sem dados para exibir", ha="center", va="center")
        ax.set_axis_off()
        return

    labels = [d[0] for d in data]
    values = [d[1] for d in data]
    total = sum(values)

    def autopct_fmt(pct: float) -> str:
        val = pct * total / 100.0
        return f"{pct:.1f}%\n{format_currency(val)}"

    _wedges, _texts, autotexts = ax.pie(
        values,
        labels=None,
        autopct=autopct_fmt,
        startangle=90,
        pctdistance=0.72,
        textprops={"fontsize": 9},
        wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_fontweight("600")

    ax.legend(
        _wedges,
        [f"{lbl}: {format_currency(v)}" for lbl, v in zip(labels, values)],
        title="Categoria e valor",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        frameon=True,
    )

    ax.set_title(
        "Assinaturas por categoria + demais gastos avulsos\n"
        "(fatias: % e R$; legenda repete nome e valor)"
    )
