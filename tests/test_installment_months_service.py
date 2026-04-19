"""Testes de competência mensal de parcelamentos em conta."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.models.installment import Installment
from app.services import installment_months_service, installments_service


def _seed_account() -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta T', 1000.0)"
        )
        return int(cur.lastrowid)


def test_set_month_status_sequential_months(test_db_path: Path) -> None:
    aid = _seed_account()
    iid = installments_service.create(
        Installment(
            id=None,
            nome_fatura="Compra X",
            cartao_id=None,
            mes_referencia="2026-01",
            valor_parcela=50.0,
            total_parcelas=3,
            parcelas_pagas=0,
            account_id=aid,
        )
    )

    installment_months_service.set_month_status(iid, "2026-01", True)
    inst = installments_service.get(iid)
    assert inst is not None
    assert inst.parcelas_pagas == 1
    assert inst.status == "ativo"
    assert installment_months_service.is_paid(iid, "2026-01")

    installment_months_service.set_month_status(iid, "2026-02", True)
    inst = installments_service.get(iid)
    assert inst is not None
    assert inst.parcelas_pagas == 2
    assert installment_months_service.is_paid(iid, "2026-02")

    installment_months_service.set_month_status(iid, "2026-02", False)
    inst = installments_service.get(iid)
    assert inst is not None
    assert inst.parcelas_pagas == 1
    assert not installment_months_service.is_paid(iid, "2026-02")


def test_set_month_status_out_of_order_rejected(test_db_path: Path) -> None:
    aid = _seed_account()
    iid = installments_service.create(
        Installment(
            id=None,
            nome_fatura="Compra Y",
            cartao_id=None,
            mes_referencia="2026-01",
            valor_parcela=10.0,
            total_parcelas=3,
            parcelas_pagas=0,
            account_id=aid,
        )
    )

    installment_months_service.set_month_status(iid, "2026-02", True)
    inst = installments_service.get(iid)
    assert inst is not None
    assert inst.parcelas_pagas == 0
    assert not installment_months_service.is_paid(iid, "2026-02")


def test_set_month_status_last_parcel_quitado(test_db_path: Path) -> None:
    aid = _seed_account()
    iid = installments_service.create(
        Installment(
            id=None,
            nome_fatura="Compra Z",
            cartao_id=None,
            mes_referencia="2026-01",
            valor_parcela=25.0,
            total_parcelas=2,
            parcelas_pagas=0,
            account_id=aid,
        )
    )

    installment_months_service.set_month_status(iid, "2026-01", True)
    installment_months_service.set_month_status(iid, "2026-02", True)
    inst = installments_service.get(iid)
    assert inst is not None
    assert inst.parcelas_pagas == 2
    assert inst.status == "quitado"
