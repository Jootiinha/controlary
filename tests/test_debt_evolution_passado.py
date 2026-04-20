"""Saldo devedor na janela Cartão: passado linear diminui até o atual."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.charts.debt_evolution import fetch_data
from app.database.connection import transaction
from app.models.installment import Installment
from app.services import installments_service


def test_debt_decreases_along_past_months_linear(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO cards (nome, dia_pagamento_fatura) VALUES ('Cartão D', 10)"
        )
        cid = int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])

    installments_service.create(
        Installment(
            id=None,
            nome_fatura="Dívida",
            cartao_id=cid,
            mes_referencia="2026-01",
            valor_parcela=100.0,
            total_parcelas=12,
            parcelas_pagas=3,
        )
    )

    current = "2026-04"
    data = dict(fetch_data(current))

    assert data["2026-02"] > data["2026-03"]
    assert data["2026-03"] == pytest.approx(data[current])
