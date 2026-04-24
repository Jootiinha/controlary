"""Próximas entradas: renda pendente no horizonte."""
from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

from app.database.connection import transaction
from app.services import calendar_service, income_months_service


def test_upcoming_receivables_lists_pending_income(test_db_path: Path) -> None:
    today = date.today()
    _, lastd = calendar.monthrange(today.year, today.month)
    dia = min(today.day + 3, lastd)
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO income_sources (
                nome, valor_mensal, ativo, dia_recebimento, tipo
            ) VALUES ('Salário extra', 100.0, 1, ?, 'recorrente')
            """,
            (dia,),
        )
    evs = calendar_service.upcoming_receivables(14)
    assert any(e.tipo == "renda" and "Salário extra" in e.titulo for e in evs)


def test_upcoming_receivables_excludes_received(test_db_path: Path) -> None:
    today = date.today()
    _, lastd = calendar.monthrange(today.year, today.month)
    dia = min(today.day + 2, lastd)
    ym = f"{today.year:04d}-{today.month:02d}"
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('C', 0)",
        )
        conn.execute(
            """
            INSERT INTO income_sources (
                nome, valor_mensal, ativo, dia_recebimento, tipo, account_id
            ) VALUES ('Bónus', 200.0, 1, ?, 'recorrente', 1)
            """,
            (dia,),
        )
        row = conn.execute("SELECT last_insert_rowid() AS id").fetchone()
        sid = int(row["id"])
    income_months_service.set_month_status(sid, ym, recebido=True, valor_efetivo=200.0)
    evs = calendar_service.upcoming_receivables(14)
    assert not any(e.tipo == "renda" and e.ref_id == sid for e in evs)
