"""Testes de gastos fixos, competência mensal e livro-caixa."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.fixed_expense import FixedExpense
from app.services import accounts_service, fixed_expenses_service


def _seed_account(name: str = "Conta F") -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES (?, 3000.0)", (name,)
        )
        return int(cur.lastrowid)


def _ledger_fixed(fe_id: int, ano_mes: str) -> list:
    key = accounts_service.transaction_key_fixed(fe_id, ano_mes)
    with transaction() as conn:
        rows = conn.execute(
            "SELECT account_id, valor, origem FROM account_transactions WHERE transaction_key = ?",
            (key,),
        ).fetchall()
    return [dict(r) for r in rows]


def test_create_list_active_get(test_db_path: Path) -> None:
    aid = _seed_account()
    fid = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Aluguel",
            valor_mensal=1200.0,
            dia_referencia=5,
            forma_pagamento="Pix",
            conta_id=aid,
        )
    )
    fe = fixed_expenses_service.get(fid)
    assert fe is not None
    assert fe.nome == "Aluguel"
    assert fe.conta_nome == "Conta F"
    active = fixed_expenses_service.list_active()
    assert len(active) == 1
    assert active[0].id == fid


def test_set_month_pago_com_conta_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    fid = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Luz",
            valor_mensal=200.0,
            dia_referencia=10,
            forma_pagamento="Débito",
            conta_id=aid,
        )
    )
    fixed_expenses_service.set_month_status(fid, "2026-04", True)
    assert fixed_expenses_service.is_paid(fid, "2026-04")
    rows = _ledger_fixed(fid, "2026-04")
    assert len(rows) == 1
    assert rows[0]["account_id"] == aid
    assert rows[0]["valor"] == -200.0
    assert rows[0]["origem"] == "fixo"


def test_set_month_pago_valor_efetivo(test_db_path: Path) -> None:
    aid = _seed_account()
    fid = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Água",
            valor_mensal=80.0,
            dia_referencia=8,
            forma_pagamento="Pix",
            conta_id=aid,
        )
    )
    fixed_expenses_service.set_month_status(
        fid, "2026-04", True, valor_efetivo=95.5
    )
    assert fixed_expenses_service.get_valor_efetivo(fid, "2026-04") == 95.5
    rows = _ledger_fixed(fid, "2026-04")
    assert rows[0]["valor"] == -95.5


def test_set_month_pago_false_remove_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    fid = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Gás",
            valor_mensal=40.0,
            dia_referencia=1,
            forma_pagamento="Pix",
            conta_id=aid,
        )
    )
    fixed_expenses_service.set_month_status(fid, "2026-03", True)
    fixed_expenses_service.set_month_status(fid, "2026-03", False)
    assert not fixed_expenses_service.is_paid(fid, "2026-03")
    assert _ledger_fixed(fid, "2026-03") == []


def test_set_month_conta_debito_override(test_db_path: Path) -> None:
    aid1 = _seed_account("A1")
    aid2 = _seed_account("A2")
    fid = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Sem conta no cadastro",
            valor_mensal=25.0,
            dia_referencia=12,
            forma_pagamento="Pix",
            conta_id=None,
        )
    )
    fixed_expenses_service.set_month_status(
        fid, "2026-04", True, conta_debito_id=aid2
    )
    rows = _ledger_fixed(fid, "2026-04")
    assert len(rows) == 1
    assert rows[0]["account_id"] == aid2
    assert rows[0]["valor"] == -25.0


def test_sum_unpaid_and_sum_paid_for_month(test_db_path: Path) -> None:
    aid = _seed_account()
    f1 = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Fixo A",
            valor_mensal=100.0,
            dia_referencia=1,
            forma_pagamento="Pix",
            conta_id=aid,
        )
    )
    f2 = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Fixo B",
            valor_mensal=50.0,
            dia_referencia=2,
            forma_pagamento="Pix",
            conta_id=aid,
        )
    )
    assert fixed_expenses_service.sum_unpaid_for_month("2026-07") == 150.0
    fixed_expenses_service.set_month_status(f1, "2026-07", True)
    assert fixed_expenses_service.sum_unpaid_for_month("2026-07") == 50.0
    assert fixed_expenses_service.sum_paid_for_month("2026-07") == 100.0
    fixed_expenses_service.set_month_status(f2, "2026-07", True, valor_efetivo=55.0)
    assert fixed_expenses_service.sum_unpaid_for_month("2026-07") == 0.0
    assert fixed_expenses_service.sum_paid_for_month("2026-07") == 155.0


def test_delete_remove_ledger_prefix(test_db_path: Path) -> None:
    aid = _seed_account()
    fid = fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Internet",
            valor_mensal=99.0,
            dia_referencia=20,
            forma_pagamento="Pix",
            conta_id=aid,
        )
    )
    fixed_expenses_service.set_month_status(fid, "2026-04", True)
    assert _ledger_fixed(fid, "2026-04")
    fixed_expenses_service.delete(fid)
    assert fixed_expenses_service.get(fid) is None
    assert _ledger_fixed(fid, "2026-04") == []


def test_update_sem_id_raises(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="sem id"):
        fixed_expenses_service.update(
            FixedExpense(
                id=None,
                nome="x",
                valor_mensal=1.0,
                dia_referencia=1,
                forma_pagamento="Pix",
                conta_id=_seed_account(),
            )
        )


def test_count_active(test_db_path: Path) -> None:
    aid = _seed_account()
    fixed_expenses_service.create(
        FixedExpense(
            id=None,
            nome="Ativo",
            valor_mensal=10.0,
            dia_referencia=1,
            forma_pagamento="Pix",
            conta_id=aid,
        )
    )
    assert fixed_expenses_service.count_active() == 1
