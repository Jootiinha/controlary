"""Testes de investimentos e snapshots."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.investment import Investment
from app.services import investments_service


def _bank() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Corretora', 0)"
        )
        return int(cur.lastrowid)


def test_create_get_list_total_aplicado(test_db_path: Path) -> None:
    bid = _bank()
    iid = investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="CDB",
            tipo="Renda fixa",
            valor_aplicado=10000.0,
            data_aplicacao="2026-01-15",
        )
    )
    inv = investments_service.get(iid)
    assert inv is not None
    assert inv.nome == "CDB"
    assert inv.banco_nome == "Corretora"
    assert investments_service.total_aplicado() == 10000.0
    assert len(investments_service.list_all()) == 1


def test_evolution_series_and_snapshots(test_db_path: Path) -> None:
    bid = _bank()
    iid = investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="Tesouro",
            tipo="SELIC",
            valor_aplicado=5000.0,
            data_aplicacao="2026-02-01",
        )
    )
    investments_service.add_snapshot(iid, "2026-03-01", 5100.0)
    investments_service.add_snapshot(iid, "2026-04-01", 5200.0)
    series = investments_service.evolution_series(iid)
    assert series[0] == ("2026-02-01", 5000.0)
    assert series[-1] == ("2026-04-01", 5200.0)
    snaps = investments_service.list_snapshots(iid)
    assert len(snaps) == 2
    assert snaps[1].valor_atual == 5200.0


def test_last_value_and_gain(test_db_path: Path) -> None:
    bid = _bank()
    iid = investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="Fundo",
            tipo="Multimercado",
            valor_aplicado=2000.0,
            data_aplicacao="2026-01-10",
        )
    )
    investments_service.add_snapshot(iid, "2026-04-01", 2150.0)
    last, gain = investments_service.last_value_and_gain(iid)
    assert last == 2150.0
    assert gain == 150.0


def test_portfolio_carteira_gain_metrics(test_db_path: Path) -> None:
    bid = _bank()
    i1 = investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="A",
            tipo="RF",
            valor_aplicado=1000.0,
            data_aplicacao="2026-01-01",
        )
    )
    i2 = investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="B",
            tipo="RV",
            valor_aplicado=500.0,
            data_aplicacao="2026-01-01",
        )
    )
    investments_service.add_snapshot(i1, "2026-04-01", 1100.0)
    investments_service.add_snapshot(i2, "2026-04-01", 400.0)
    ganho, pct = investments_service.portfolio_carteira_gain_metrics()
    assert ganho == pytest.approx(0.0)
    assert pct is not None
    assert pct == pytest.approx(0.0, abs=0.01)


def test_portfolio_patrimonio_series(test_db_path: Path) -> None:
    bid = _bank()
    iid = investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="Único",
            tipo="RF",
            valor_aplicado=100.0,
            data_aplicacao="2026-03-01",
        )
    )
    investments_service.add_snapshot(iid, "2026-04-01", 110.0)
    ser = investments_service.portfolio_patrimonio_series()
    assert len(ser) >= 2
    assert ser[-1][1] == 110.0


def test_delete(test_db_path: Path) -> None:
    bid = _bank()
    iid = investments_service.create(
        Investment(
            id=None,
            banco_id=bid,
            nome="Temp",
            tipo="RF",
            valor_aplicado=1.0,
            data_aplicacao="2026-01-01",
        )
    )
    investments_service.add_snapshot(iid, "2026-02-01", 1.0)
    investments_service.delete(iid)
    assert investments_service.get(iid) is None
    assert investments_service.list_snapshots(iid) == []


def test_update_sem_id_raises(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="sem id"):
        investments_service.update(
            Investment(
                id=None,
                banco_id=_bank(),
                nome="x",
                tipo="RF",
                valor_aplicado=1.0,
                data_aplicacao="2026-01-01",
            )
        )
