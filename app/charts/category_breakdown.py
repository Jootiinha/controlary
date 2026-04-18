"""Distribuição por categoria: pagamentos + assinaturas ativas."""
from __future__ import annotations

from app.database.connection import transaction
from app.utils.formatting import format_currency


def fetch_data() -> list[tuple[str, float]]:
    with transaction() as conn:
        items: dict[str, float] = {}
        for r in conn.execute(
            """
            SELECT COALESCE(cat.nome, 'Sem categoria') AS nm,
                   COALESCE(SUM(p.valor), 0) AS t
              FROM payments p
              LEFT JOIN categories cat ON cat.id = p.category_id
             GROUP BY nm
            """
        ).fetchall():
            nm = r["nm"]
            items[nm] = items.get(nm, 0.0) + float(r["t"] or 0)

        for r in conn.execute(
            """
            SELECT COALESCE(cat.nome, 'Sem categoria') AS nm,
                   COALESCE(SUM(s.valor_mensal), 0) AS t
              FROM subscriptions s
              LEFT JOIN categories cat ON cat.id = s.category_id
             WHERE s.status = 'ativa'
             GROUP BY nm
            """
        ).fetchall():
            nm = r["nm"]
            items[nm] = items.get(nm, 0.0) + float(r["t"] or 0)

    out = [(k, v) for k, v in items.items() if v > 0]
    out.sort(key=lambda x: x[1], reverse=True)
    return out


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
        title="Categoria",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        frameon=True,
    )

    ax.set_title(
        "Categorias · pagamentos acumulados + assinaturas ativas (valor mensal)"
    )
