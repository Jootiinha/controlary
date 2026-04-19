"""Calendário e próximos vencimentos."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from app.database.connection import transaction
from app.services import calendar_service


def test_upcoming_payables_inclui_pagamento_avulso_futuro_em_conta(
    test_db_path: Path,
) -> None:
    hoje = date.today()
    daqui_tres = (hoje + timedelta(days=3)).isoformat()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta X', 0)"
        )
        conn.execute(
            """
            INSERT INTO payments (
                valor, descricao, data, conta, conta_id, cartao_id, forma_pagamento
            ) VALUES (100.0, 'Prestador', ?, 'Conta X', 1, NULL, 'Pix')
            """,
            (daqui_tres,),
        )

    evs = calendar_service.upcoming_payables(calendar_service.UPCOMING_HORIZON_DAYS)
    tipos_pag = [e for e in evs if e.tipo == "pagamento"]
    assert len(tipos_pag) == 1
    assert tipos_pag[0].titulo.startswith("Prestador")
    assert tipos_pag[0].valor == 100.0
