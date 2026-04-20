"""Próximas entradas: renda pendente no horizonte."""
from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

from app.database.connection import transaction
from app.services import calendar_service


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
