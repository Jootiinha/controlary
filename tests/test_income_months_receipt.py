"""Recebimento de renda: valor efetivo e conta por competência no livro-caixa."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.models.income_source import IncomeSource
from app.services import accounts_service, income_months_service, income_sources_service


def test_receipt_other_account_and_valor(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 0)")
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('B', 0)")
    src = IncomeSource(
        id=None,
        nome="Salário",
        valor_mensal=3000.0,
        ativo=True,
        dia_recebimento=10,
        account_id=1,
        tipo="recorrente",
    )
    sid = income_sources_service.create(src)
    key = accounts_service.transaction_key_income(sid, "2026-03")
    income_months_service.set_month_status(
        sid,
        "2026-03",
        recebido=True,
        valor_efetivo=2850.5,
        conta_recebimento_id=2,
    )
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT account_id, valor FROM account_transactions
             WHERE transaction_key = ?
            """,
            (key,),
        ).fetchone()
        assert row is not None
        assert int(row["account_id"]) == 2
        assert abs(float(row["valor"]) - 2850.5) < 0.01
        im = conn.execute(
            """
            SELECT valor_efetivo, conta_recebimento_id FROM income_months
             WHERE income_source_id = ? AND ano_mes = '2026-03'
            """,
            (sid,),
        ).fetchone()
        assert im is not None
        assert abs(float(im["valor_efetivo"]) - 2850.5) < 0.01
        assert int(im["conta_recebimento_id"]) == 2


def test_receipt_switch_account_same_month(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 0)")
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('B', 0)")
    src = IncomeSource(
        id=None,
        nome="Extra",
        valor_mensal=100.0,
        ativo=True,
        dia_recebimento=5,
        account_id=1,
        tipo="avulsa",
        mes_referencia="2026-04",
    )
    sid = income_sources_service.create(src)
    key = accounts_service.transaction_key_income(sid, "2026-04")
    income_months_service.set_month_status(
        sid, "2026-04", recebido=True, conta_recebimento_id=1
    )
    with transaction() as conn:
        assert (
            int(
                conn.execute(
                    "SELECT account_id FROM account_transactions WHERE transaction_key = ?",
                    (key,),
                ).fetchone()["account_id"]
            )
            == 1
        )
    income_months_service.set_month_status(
        sid, "2026-04", recebido=True, valor_efetivo=100.0, conta_recebimento_id=2
    )
    with transaction() as conn:
        n = int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM account_transactions WHERE transaction_key = ?",
                (key,),
            ).fetchone()["n"]
        )
        assert n == 1
        row = conn.execute(
            "SELECT account_id FROM account_transactions WHERE transaction_key = ?",
            (key,),
        ).fetchone()
        assert int(row["account_id"]) == 2


def test_get_month_record_and_resolved(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 0)")
    src = IncomeSource(
        id=None,
        nome="X",
        valor_mensal=10.0,
        ativo=True,
        dia_recebimento=5,
        account_id=1,
        tipo="recorrente",
    )
    sid = income_sources_service.create(src)
    assert income_months_service.get_month_record(sid, "2026-05") is None
    income_months_service.set_month_status(
        sid, "2026-05", recebido=True, valor_efetivo=9.0, conta_recebimento_id=None
    )
    r = income_months_service.get_month_record(sid, "2026-05")
    assert r is not None
    assert r[0] is True
    assert abs(r[1] - 9.0) < 0.01
    assert r[2] is None
    assert income_months_service.resolved_account_id(1, None) == 1
