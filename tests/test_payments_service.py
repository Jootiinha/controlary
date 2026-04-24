"""Testes de CRUD de pagamentos e livro-caixa (conta)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.payment import Payment
from app.services import accounts_service, payments_service


def _seed_account() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta P', 2000.0)"
        )
        return int(cur.lastrowid)


def _seed_card(account_id: int) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO cards (nome, account_id, dia_pagamento_fatura) VALUES ('Visa', ?, 10)",
            (account_id,),
        )
        return int(cur.lastrowid)


def _ledger_rows_for_payment(payment_id: int) -> list:
    key = accounts_service.transaction_key_payment(payment_id)
    with transaction() as conn:
        rows = conn.execute(
            """
            SELECT account_id, valor, data, origem, transaction_key, descricao
              FROM account_transactions
             WHERE transaction_key = ?
            """,
            (key,),
        ).fetchall()
    return [dict(r) for r in rows]


def test_create_conta_record_ledger_inserts_payment_and_transaction(
    test_db_path: Path,
) -> None:
    aid = _seed_account()
    pid = payments_service.create(
        Payment(
            id=None,
            valor=75.5,
            descricao="Compra teste",
            data="2026-04-10",
            conta_id=aid,
            forma_pagamento="Pix",
        ),
        record_ledger=True,
    )
    assert pid > 0
    p = payments_service.get(pid)
    assert p is not None
    assert p.valor == 75.5
    assert p.conta_id == aid
    assert p.conta_nome == "Conta P"
    assert p.cartao_id is None

    rows = _ledger_rows_for_payment(pid)
    assert len(rows) == 1
    assert rows[0]["account_id"] == aid
    assert rows[0]["valor"] == -75.5
    assert rows[0]["data"] == "2026-04-10"
    assert rows[0]["origem"] == "pagamento"


def test_create_conta_record_ledger_false_no_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    pid = payments_service.create(
        Payment(
            id=None,
            valor=10.0,
            descricao="Espelho",
            data="2026-04-01",
            conta_id=aid,
            forma_pagamento="Débito",
        ),
        record_ledger=False,
    )
    assert _ledger_rows_for_payment(pid) == []


def test_create_cartao_sem_livro_caixa(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = _seed_card(aid)
    pid = payments_service.create(
        Payment(
            id=None,
            valor=100.0,
            descricao="No cartão",
            data="2026-04-15",
            conta_id=None,
            forma_pagamento="Crédito",
            cartao_id=cid,
        ),
        record_ledger=True,
    )
    assert _ledger_rows_for_payment(pid) == []
    p = payments_service.get(pid)
    assert p is not None
    assert p.cartao_id == cid
    assert p.cartao_nome == "Visa"


def test_validate_origin_both_none(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="conta bancária ou cartão"):
        payments_service.create(
            Payment(
                id=None,
                valor=1.0,
                descricao="x",
                data="2026-04-01",
                conta_id=None,
                forma_pagamento="Pix",
                cartao_id=None,
            )
        )


def test_validate_origin_both_set(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = _seed_card(aid)
    with pytest.raises(ValueError, match="conta bancária ou cartão"):
        payments_service.create(
            Payment(
                id=None,
                valor=1.0,
                descricao="x",
                data="2026-04-01",
                conta_id=aid,
                forma_pagamento="Pix",
                cartao_id=cid,
            )
        )


def test_create_conta_invalida(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="Conta inválida"):
        payments_service.create(
            Payment(
                id=None,
                valor=1.0,
                descricao="x",
                data="2026-04-01",
                conta_id=999,
                forma_pagamento="Pix",
            )
        )


def test_list_between_and_list_all(test_db_path: Path) -> None:
    aid = _seed_account()
    payments_service.create(
        Payment(
            id=None,
            valor=10.0,
            descricao="A",
            data="2026-03-31",
            conta_id=aid,
            forma_pagamento="Pix",
        )
    )
    payments_service.create(
        Payment(
            id=None,
            valor=20.0,
            descricao="B",
            data="2026-04-05",
            conta_id=aid,
            forma_pagamento="Pix",
        )
    )
    payments_service.create(
        Payment(
            id=None,
            valor=30.0,
            descricao="C",
            data="2026-04-20",
            conta_id=aid,
            forma_pagamento="Pix",
        )
    )
    mid = payments_service.list_between(date(2026, 4, 1), date(2026, 4, 30))
    assert len(mid) == 2
    assert [p.descricao for p in mid] == ["B", "C"]
    all_p = payments_service.list_all()
    assert len(all_p) == 3
    assert all_p[0].descricao == "C"


def test_get_missing_returns_none(test_db_path: Path) -> None:
    assert payments_service.get(99999) is None


def test_update_conta_adjusts_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    pid = payments_service.create(
        Payment(
            id=None,
            valor=50.0,
            descricao="Original",
            data="2026-04-01",
            conta_id=aid,
            forma_pagamento="Pix",
        ),
        record_ledger=True,
    )
    payments_service.update(
        Payment(
            id=pid,
            valor=80.0,
            descricao="Ajustado",
            data="2026-04-02",
            conta_id=aid,
            forma_pagamento="Pix",
        )
    )
    rows = _ledger_rows_for_payment(pid)
    assert len(rows) == 1
    assert rows[0]["valor"] == -80.0
    assert rows[0]["data"] == "2026-04-02"


def test_update_conta_sem_ledger_previo_nao_cria_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    pid = payments_service.create(
        Payment(
            id=None,
            valor=40.0,
            descricao="Sem ledger",
            data="2026-04-01",
            conta_id=aid,
            forma_pagamento="Pix",
        ),
        record_ledger=False,
    )
    payments_service.update(
        Payment(
            id=pid,
            valor=99.0,
            descricao="Novo",
            data="2026-04-03",
            conta_id=aid,
            forma_pagamento="Pix",
        )
    )
    assert _ledger_rows_for_payment(pid) == []


def test_update_to_cartao_remove_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    cid = _seed_card(aid)
    pid = payments_service.create(
        Payment(
            id=None,
            valor=25.0,
            descricao="Na conta",
            data="2026-04-01",
            conta_id=aid,
            forma_pagamento="Pix",
        ),
        record_ledger=True,
    )
    assert len(_ledger_rows_for_payment(pid)) == 1
    payments_service.update(
        Payment(
            id=pid,
            valor=25.0,
            descricao="No cartão",
            data="2026-04-01",
            conta_id=None,
            forma_pagamento="Crédito",
            cartao_id=cid,
        )
    )
    assert _ledger_rows_for_payment(pid) == []
    p = payments_service.get(pid)
    assert p is not None
    assert p.cartao_id == cid


def test_delete_removes_payment_and_ledger(test_db_path: Path) -> None:
    aid = _seed_account()
    pid = payments_service.create(
        Payment(
            id=None,
            valor=15.0,
            descricao="Apagar",
            data="2026-04-01",
            conta_id=aid,
            forma_pagamento="Pix",
        ),
        record_ledger=True,
    )
    assert len(_ledger_rows_for_payment(pid)) == 1
    payments_service.delete(pid)
    assert payments_service.get(pid) is None
    assert _ledger_rows_for_payment(pid) == []


def test_update_sem_id_raises(test_db_path: Path) -> None:
    with pytest.raises(ValueError, match="sem id"):
        payments_service.update(
            Payment(
                id=None,
                valor=1.0,
                descricao="x",
                data="2026-04-01",
                conta_id=_seed_account(),
                forma_pagamento="Pix",
            )
        )
