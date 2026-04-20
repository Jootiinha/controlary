"""Realizado dos gráficos da aba Cartão: cronograma de parcelas por mês."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.charts.invoice_evolution import build_realizado_map
from app.database.connection import transaction
from app.models.installment import Installment
from app.services import installments_service


def test_realizado_schedule_spreads_over_months(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO cards (nome, dia_pagamento_fatura) VALUES ('Cartão T', 10)"
        )
        cid = int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])

    installments_service.create(
        Installment(
            id=None,
            nome_fatura="Compra",
            cartao_id=cid,
            mes_referencia="2026-01",
            valor_parcela=100.0,
            total_parcelas=12,
            parcelas_pagas=0,
        )
    )

    ref = "2026-04"
    d = build_realizado_map(ref, "all")

    assert d.get("2026-01") == pytest.approx(100.0)
    assert d.get("2026-02") == pytest.approx(100.0)
    assert d.get("2026-03") == pytest.approx(100.0)
    assert d.get("2026-04") == pytest.approx(100.0)
