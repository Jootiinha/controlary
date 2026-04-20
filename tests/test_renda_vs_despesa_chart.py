"""Série renda vs despesa: janela 3+9 e avulsas na renda esperada."""
from __future__ import annotations

from pathlib import Path

from app.charts.renda_vs_despesa import build_series
from app.database.connection import transaction
from app.utils.formatting import current_month


def test_build_series_length_and_avulsa_in_renda(test_db_path: Path) -> None:
    ym = current_month()
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO income_sources (
                nome, valor_mensal, ativo, dia_recebimento, tipo, mes_referencia
            ) VALUES ('Extra', 333.0, 1, 20, 'avulsa', ?)
            """,
            (ym,),
        )
    _labels, r_vals, g_vals, keys_past, keys_fut = build_series(months_past=3, months_future=9)
    keys = keys_past + keys_fut
    assert len(keys) == 12
    assert len(r_vals) == 12
    assert ym in keys
    idx = keys.index(ym)
    assert r_vals[idx] == 333.0
    assert len(g_vals) == 12
