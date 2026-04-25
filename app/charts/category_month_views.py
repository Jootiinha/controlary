"""Pizza por categoria: livro-caixa no mês e composição de custo (cost_of_living)."""
from __future__ import annotations

import re
from typing import Any, Callable

from matplotlib.patches import Wedge

from app.database.connection import transaction
from app.utils.formatting import current_month, format_currency, format_month_br

_CAT_OTHER = "Sem categoria"


def _merge_amounts(items: dict[str, float], pairs: list[tuple[str, float]]) -> None:
    for nm, v in pairs:
        if v <= 0:
            continue
        items[nm] = items.get(nm, 0.0) + v


def _category_name_from_id(conn, category_id: int | None) -> str:
    if category_id is None:
        return _CAT_OTHER
    row = conn.execute(
        "SELECT nome FROM categories WHERE id = ?", (int(category_id),)
    ).fetchone()
    return (row["nome"] or _CAT_OTHER) if row else _CAT_OTHER


def _card_component_lines(
    conn, cartao_id: int, ano_mes: str
) -> list[tuple[str, float]]:
    lines: list[tuple[str, float]] = []
    for r in conn.execute(
        """
        SELECT i.valor_parcela AS v, COALESCE(cat.nome, ?) AS nm
          FROM installments i
          LEFT JOIN categories cat ON cat.id = i.category_id
         WHERE i.status = 'ativo'
           AND i.cartao_id = ?
           AND i.mes_referencia = ?
        """,
        (_CAT_OTHER, cartao_id, ano_mes),
    ).fetchall():
        lines.append((str(r["nm"]), float(r["v"] or 0)))
    for r in conn.execute(
        """
        SELECT s.valor_mensal AS v, COALESCE(cat.nome, ?) AS nm
          FROM subscriptions s
          LEFT JOIN categories cat ON cat.id = s.category_id
         WHERE s.status = 'ativa'
           AND s.card_id = ?
        """,
        (_CAT_OTHER, cartao_id),
    ).fetchall():
        lines.append((str(r["nm"]), float(r["v"] or 0)))
    for r in conn.execute(
        """
        SELECT p.valor AS v, COALESCE(cat.nome, ?) AS nm
          FROM payments p
          LEFT JOIN categories cat ON cat.id = p.category_id
         WHERE p.cartao_id = ?
           AND substr(p.data, 1, 7) = ?
        """,
        (_CAT_OTHER, cartao_id, ano_mes),
    ).fetchall():
        lines.append((str(r["nm"]), float(r["v"] or 0)))
    return lines


def _distribute_proportional(
    lines: list[tuple[str, float]], total: float
) -> list[tuple[str, float]]:
    if total <= 0:
        return []
    wsum = sum(w for _, w in lines)
    if wsum <= 0:
        return [(_CAT_OTHER, total)]
    out: list[tuple[str, float]] = []
    for nm, w in lines:
        if w <= 0:
            continue
        out.append((nm, total * (w / wsum)))
    return out


def _ledger_invoice_distribution(
    conn, invoice_id: int, amount: float
) -> list[tuple[str, float]]:
    row = conn.execute(
        """
        SELECT cartao_id, ano_mes
          FROM card_invoices
         WHERE id = ?
        """,
        (invoice_id,),
    ).fetchone()
    if not row:
        return [(_CAT_OTHER, amount)]
    cid = int(row["cartao_id"])
    ym = str(row["ano_mes"])
    lines = _card_component_lines(conn, cid, ym)
    return _distribute_proportional(lines, amount)


def _parse_ledger_key(
    conn, transaction_key: str, amount: float
) -> list[tuple[str, float]]:
    if amount <= 0:
        return []

    if transaction_key.startswith("payment:"):
        m = re.match(r"^payment:(\d+)$", transaction_key)
        if not m:
            return [(_CAT_OTHER, amount)]
        pid = int(m.group(1))
        row = conn.execute(
            "SELECT category_id FROM payments WHERE id = ?", (pid,)
        ).fetchone()
        cid = int(row["category_id"]) if row and row["category_id"] is not None else None
        return [(_category_name_from_id(conn, cid), amount)]

    if transaction_key.startswith("invoice:"):
        m = re.match(r"^invoice:(\d+)$", transaction_key)
        if not m:
            return [(_CAT_OTHER, amount)]
        return _ledger_invoice_distribution(conn, int(m.group(1)), amount)

    if transaction_key.startswith("fixed:"):
        m = re.match(r"^fixed:(\d+):(\d{4}-\d{2})$", transaction_key)
        if not m:
            return [(_CAT_OTHER, amount)]
        fe_id = int(m.group(1))
        row = conn.execute(
            "SELECT category_id FROM fixed_expenses WHERE id = ?", (fe_id,)
        ).fetchone()
        cat_id = int(row["category_id"]) if row and row["category_id"] is not None else None
        return [(_category_name_from_id(conn, cat_id), amount)]

    if transaction_key.startswith("subscription:"):
        m = re.match(r"^subscription:(\d+):(\d{4}-\d{2})$", transaction_key)
        if not m:
            return [(_CAT_OTHER, amount)]
        sid = int(m.group(1))
        row = conn.execute(
            "SELECT category_id FROM subscriptions WHERE id = ?", (sid,)
        ).fetchone()
        cat_id = int(row["category_id"]) if row and row["category_id"] is not None else None
        return [(_category_name_from_id(conn, cat_id), amount)]

    if transaction_key.startswith("installment:"):
        m = re.match(r"^installment:(\d+):(\d{4}-\d{2})$", transaction_key)
        if not m:
            return [(_CAT_OTHER, amount)]
        iid = int(m.group(1))
        row = conn.execute(
            "SELECT category_id FROM installments WHERE id = ?", (iid,)
        ).fetchone()
        cat_id = int(row["category_id"]) if row and row["category_id"] is not None else None
        return [(_category_name_from_id(conn, cat_id), amount)]

    if transaction_key.startswith("income:"):
        return [(_CAT_OTHER, amount)]

    if transaction_key.startswith("adjustment:"):
        return []

    return [(_CAT_OTHER, amount)]


def fetch_ledger_by_category(ano_mes: str) -> list[tuple[str, float]]:
    items: dict[str, float] = {}
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT valor, transaction_key
              FROM account_transactions
             WHERE substr(data, 1, 7) = ?
               AND valor < 0
               AND NOT (
                   COALESCE(origem, '') = 'ajuste'
                   OR COALESCE(transaction_key, '') LIKE 'adjustment:%'
               )
            """,
            (ano_mes,),
        ).fetchall()
        for row in rows:
            amt = abs(float(row["valor"] or 0))
            key = str(row["transaction_key"] or "")
            pairs = _parse_ledger_key(conn, key, amt)
            _merge_amounts(items, pairs)

    out = [(k, round(v, 2)) for k, v in items.items() if v > 0]
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def fetch_cost_of_living_by_category(ano_mes: str) -> list[tuple[str, float]]:
    items: dict[str, float] = {}
    with transaction() as conn:
        for r in conn.execute(
            """
            SELECT COALESCE(cat.nome, ?) AS nm,
                   COALESCE(SUM(p.valor), 0) AS t
              FROM payments p
              LEFT JOIN categories cat ON cat.id = p.category_id
             WHERE substr(p.data, 1, 7) = ?
               AND p.cartao_id IS NULL
             GROUP BY COALESCE(cat.nome, ?)
            """,
            (_CAT_OTHER, ano_mes, _CAT_OTHER),
        ).fetchall():
            v = float(r["t"] or 0)
            if v > 0:
                items[str(r["nm"])] = items.get(str(r["nm"]), 0.0) + v

        for r in conn.execute(
            """
            SELECT COALESCE(cat.nome, ?) AS nm,
                   COALESCE(SUM(s.valor_mensal), 0) AS t
              FROM subscriptions s
              LEFT JOIN categories cat ON cat.id = s.category_id
             WHERE s.status = 'ativa'
               AND s.card_id IS NULL
               AND NOT EXISTS (
                   SELECT 1 FROM subscription_months sm
                    WHERE sm.subscription_id = s.id
                      AND sm.ano_mes = ?
                      AND sm.status = 'pago'
               )
             GROUP BY COALESCE(cat.nome, ?)
            """,
            (_CAT_OTHER, ano_mes, _CAT_OTHER),
        ).fetchall():
            v = float(r["t"] or 0)
            if v > 0:
                items[str(r["nm"])] = items.get(str(r["nm"]), 0.0) + v

        for r in conn.execute(
            """
            SELECT COALESCE(cat.nome, ?) AS nm,
                   COALESCE(SUM(i.valor_parcela), 0) AS t
              FROM installments i
              LEFT JOIN categories cat ON cat.id = i.category_id
             WHERE i.status = 'ativo'
               AND i.cartao_id IS NULL
               AND i.mes_referencia = ?
               AND NOT EXISTS (
                   SELECT 1 FROM installment_months im
                    WHERE im.installment_id = i.id
                      AND im.ano_mes = ?
                      AND im.status = 'pago'
               )
             GROUP BY COALESCE(cat.nome, ?)
            """,
            (_CAT_OTHER, ano_mes, ano_mes, _CAT_OTHER),
        ).fetchall():
            v = float(r["t"] or 0)
            if v > 0:
                items[str(r["nm"])] = items.get(str(r["nm"]), 0.0) + v

        for r in conn.execute(
            """
            SELECT COALESCE(cat.nome, ?) AS nm,
                   COALESCE(SUM(f.valor_mensal), 0) AS t
              FROM fixed_expenses f
              LEFT JOIN categories cat ON cat.id = f.category_id
              LEFT JOIN fixed_expense_months m
                ON m.fixed_expense_id = f.id AND m.ano_mes = ?
             WHERE f.ativo = 1
               AND COALESCE(m.status, 'pendente') != 'pago'
             GROUP BY COALESCE(cat.nome, ?)
            """,
            (_CAT_OTHER, ano_mes, _CAT_OTHER),
        ).fetchall():
            v = float(r["t"] or 0)
            if v > 0:
                items[str(r["nm"])] = items.get(str(r["nm"]), 0.0) + v

        for cr in conn.execute("SELECT id FROM cards").fetchall():
            cid = int(cr["id"])
            inv = conn.execute(
                """
                SELECT COALESCE(valor_total, 0) AS vt
                  FROM card_invoices
                 WHERE cartao_id = ? AND ano_mes = ?
                """,
                (cid, ano_mes),
            ).fetchone()
            vt = float(inv["vt"]) if inv else 0.0

            r1 = conn.execute(
                """
                SELECT COALESCE(SUM(valor_parcela), 0) AS t
                  FROM installments
                 WHERE status = 'ativo'
                   AND cartao_id = ?
                   AND mes_referencia = ?
                """,
                (cid, ano_mes),
            ).fetchone()
            r2 = conn.execute(
                """
                SELECT COALESCE(SUM(valor_mensal), 0) AS t
                  FROM subscriptions
                 WHERE status = 'ativa'
                   AND card_id = ?
                """,
                (cid,),
            ).fetchone()
            r3 = conn.execute(
                """
                SELECT COALESCE(SUM(valor), 0) AS t
                  FROM payments
                 WHERE cartao_id = ?
                   AND substr(data, 1, 7) = ?
                """,
                (cid, ano_mes),
            ).fetchone()
            v_sug = (
                float(r1["t"] or 0)
                + float(r2["t"] or 0)
                + float(r3["t"] or 0)
            )

            lines = _card_component_lines(conn, cid, ano_mes)
            if vt > 0:
                _merge_amounts(items, _distribute_proportional(lines, vt))
            elif v_sug > 0:
                _merge_amounts(items, _distribute_proportional(lines, v_sug))

    out = [(k, round(v, 2)) for k, v in items.items() if v > 0]
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _sorted_pairs(data: list[tuple[str, float]]) -> list[tuple[str, float]]:
    out = [(k, v) for k, v in data if v > 0]
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _render_pie(
    ax,
    data: list[tuple[str, float]],
    title: str,
    subtitle: str | None = None,
) -> None:
    rows = _sorted_pairs(data)
    if not rows:
        ax.text(0.5, 0.5, "Sem dados para exibir", ha="center", va="center")
        ax.set_axis_off()
        full = f"{title} · {subtitle}" if subtitle else title
        ax.set_title(full, fontsize=9, pad=6)
        return

    labels = [d[0] for d in rows]
    values = [d[1] for d in rows]
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

    full_title = f"{title} · {subtitle}" if subtitle else title
    ax.set_title(full_title, fontsize=9, pad=6)

    def _hover_format(artist: Any, target: Any, index: int | None) -> str:
        if not isinstance(artist, Wedge):
            return ""
        idx = int(index) if index is not None else None
        if idx is None:
            wedges = [p for p in ax.patches if isinstance(p, Wedge)]
            try:
                idx = wedges.index(artist)
            except ValueError:
                return ""
        if not (0 <= idx < len(labels)):
            return ""
        val = values[idx]
        lbl = labels[idx]
        pct = 100.0 * val / total if total else 0.0
        return f"{lbl}\n{format_currency(val)}\n({pct:.1f}% do total)"

    ax._hover_format = _hover_format


def make_plot_ledger() -> Callable[..., None]:
    """Usa o mês civil atual a cada redesenho (alinhado ao dashboard)."""

    def plot(ax) -> None:
        ano_mes = current_month()
        data = fetch_ledger_by_category(ano_mes)
        _render_pie(
            ax,
            data,
            "Livro-caixa por categoria",
            format_month_br(ano_mes),
        )

    return plot


def make_plot_cost_of_living() -> Callable[..., None]:
    def plot(ax) -> None:
        ano_mes = current_month()
        data = fetch_cost_of_living_by_category(ano_mes)
        _render_pie(
            ax,
            data,
            "Composição do custo",
            format_month_br(ano_mes),
        )

    return plot
