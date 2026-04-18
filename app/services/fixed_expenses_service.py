"""Gastos fixos mensais (aluguel, luz etc.) com status pago/pendente por competência."""
from __future__ import annotations

import sqlite3
from calendar import monthrange
from datetime import date
from typing import List, Optional, Tuple

from app.database.connection import transaction
from app.models.fixed_expense import FixedExpense
from app.services import accounts_service


def _status_row(conn, fe_id: int, ano_mes: str) -> Optional[str]:
    row = conn.execute(
        """
        SELECT status FROM fixed_expense_months
         WHERE fixed_expense_id = ? AND ano_mes = ?
        """,
        (fe_id, ano_mes),
    ).fetchone()
    return row["status"] if row else None


def is_paid(fe_id: int, ano_mes: str) -> bool:
    """Sem registro = ainda não pago (previsto)."""
    with transaction() as conn:
        st = _status_row(conn, fe_id, ano_mes)
    return st == "pago"


def set_month_status(
    fe_id: int,
    ano_mes: str,
    pago: bool,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    status = "pago" if pago else "pendente"

    def _apply(c: sqlite3.Connection) -> None:
        fe = c.execute(
            """
            SELECT valor_mensal, conta_id, dia_referencia
              FROM fixed_expenses
             WHERE id = ?
            """,
            (fe_id,),
        ).fetchone()
        key = accounts_service.transaction_key_fixed(fe_id, ano_mes)
        if not pago:
            accounts_service.remove_transaction_key(key, conn=c)
        elif fe and fe["conta_id"]:
            y, m = map(int, ano_mes.split("-"))
            dia = min(int(fe["dia_referencia"] or 5), monthrange(y, m)[1])
            data = f"{y:04d}-{m:02d}-{dia:02d}"
            accounts_service.upsert_transaction(
                int(fe["conta_id"]),
                -float(fe["valor_mensal"]),
                data,
                "fixo",
                key,
                None,
                conn=c,
            )
        row = c.execute(
            """
            SELECT 1 FROM fixed_expense_months
             WHERE fixed_expense_id = ? AND ano_mes = ?
            """,
            (fe_id, ano_mes),
        ).fetchone()
        if row:
            c.execute(
                """
                UPDATE fixed_expense_months SET status = ?
                 WHERE fixed_expense_id = ? AND ano_mes = ?
                """,
                (status, fe_id, ano_mes),
            )
        else:
            c.execute(
                """
                INSERT INTO fixed_expense_months (fixed_expense_id, ano_mes, status)
                VALUES (?, ?, ?)
                """,
                (fe_id, ano_mes, status),
            )

    if conn is not None:
        _apply(conn)
    else:
        with transaction() as c:
            _apply(c)


def list_active() -> List[FixedExpense]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT f.*, a.nome AS conta_nome, cat.nome AS categoria_nome
              FROM fixed_expenses f
              LEFT JOIN accounts a ON a.id = f.conta_id
              LEFT JOIN categories cat ON cat.id = f.category_id
             WHERE f.ativo = 1
             ORDER BY f.nome COLLATE NOCASE
            """
        ).fetchall()
    return [FixedExpense.from_row(r) for r in rows]


def list_all() -> List[FixedExpense]:
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT f.*, a.nome AS conta_nome, cat.nome AS categoria_nome
              FROM fixed_expenses f
              LEFT JOIN accounts a ON a.id = f.conta_id
              LEFT JOIN categories cat ON cat.id = f.category_id
             ORDER BY f.ativo DESC, f.nome COLLATE NOCASE
            """
        ).fetchall()
    return [FixedExpense.from_row(r) for r in rows]


def get(fe_id: int) -> Optional[FixedExpense]:
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT f.*, a.nome AS conta_nome, cat.nome AS categoria_nome
              FROM fixed_expenses f
              LEFT JOIN accounts a ON a.id = f.conta_id
              LEFT JOIN categories cat ON cat.id = f.category_id
             WHERE f.id = ?
            """,
            (fe_id,),
        ).fetchone()
    return FixedExpense.from_row(row) if row else None


def create(fe: FixedExpense) -> int:
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO fixed_expenses (
                nome, valor_mensal, dia_referencia, forma_pagamento,
                conta_id, observacao, ativo, category_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fe.nome.strip(),
                fe.valor_mensal,
                fe.dia_referencia,
                fe.forma_pagamento,
                fe.conta_id,
                fe.observacao,
                1 if fe.ativo else 0,
                fe.category_id,
            ),
        )
        return int(cur.lastrowid)


def update(fe: FixedExpense) -> None:
    if fe.id is None:
        raise ValueError("Gasto fixo sem id")
    with transaction() as conn:
        conn.execute(
            """
            UPDATE fixed_expenses
               SET nome = ?, valor_mensal = ?, dia_referencia = ?, forma_pagamento = ?,
                   conta_id = ?, observacao = ?, ativo = ?, category_id = ?
             WHERE id = ?
            """,
            (
                fe.nome.strip(),
                fe.valor_mensal,
                fe.dia_referencia,
                fe.forma_pagamento,
                fe.conta_id,
                fe.observacao,
                1 if fe.ativo else 0,
                fe.category_id,
                fe.id,
            ),
        )


def delete(fe_id: int) -> None:
    with transaction() as conn:
        accounts_service.remove_transaction_keys_like_prefix(
            f"fixed:{fe_id}:", conn=conn
        )
        conn.execute("DELETE FROM fixed_expenses WHERE id = ?", (fe_id,))


def sum_unpaid_for_month(ano_mes: str) -> float:
    """Soma valores de itens ativos cuja competência não está como paga."""
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT f.valor_mensal, m.status
              FROM fixed_expenses f
              LEFT JOIN fixed_expense_months m
                ON m.fixed_expense_id = f.id AND m.ano_mes = ?
             WHERE f.ativo = 1
            """,
            (ano_mes,),
        ).fetchall()
    total = 0.0
    for r in rows:
        if r["status"] != "pago":
            total += float(r["valor_mensal"] or 0)
    return round(total, 2)


def sum_unpaid_rest_of_calendar_year() -> float:
    """Soma todos os meses do ano corrente, da competência atual até dezembro, apenas pendências."""
    d = date.today()
    y, m0 = d.year, d.month
    total = 0.0
    for m in range(m0, 13):
        ym = f"{y}-{m:02d}"
        total += sum_unpaid_for_month(ym)
    return round(total, 2)


def projection_by_month_rest_of_year() -> List[Tuple[str, float]]:
    """Lista (YYYY-MM, total pendente) do mês atual até dez/ano."""
    d = date.today()
    y, m0 = d.year, d.month
    out: List[Tuple[str, float]] = []
    for m in range(m0, 13):
        ym = f"{y}-{m:02d}"
        out.append((ym, sum_unpaid_for_month(ym)))
    return out


def count_active() -> int:
    with transaction() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM fixed_expenses WHERE ativo = 1"
        ).fetchone()
    return int(row["n"] or 0)
