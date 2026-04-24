from __future__ import annotations

from app.models.installment import Installment, schedule_parcel_amounts
from app.services import installments_service


def test_schedule_parcel_amounts_splits_cents() -> None:
    s = schedule_parcel_amounts(100.0, 3)
    assert len(s) == 3
    assert round(sum(s), 2) == 100.0
    assert sorted(s, reverse=True) == [33.34, 33.33, 33.33]


def test_preview_parcelamento_saldo_usa_cronograma() -> None:
    tot, rest, saldo, st = installments_service.preview_parcelamento(
        100.0 / 3.0, 3, 1
    )
    assert tot == 100.0
    assert rest == 2
    assert st == "ativo"
    sched = schedule_parcel_amounts(100.0, 3)
    assert saldo == round(sum(sched[1:]), 2)


def test_installment_saldo_devedor_consistente() -> None:
    inst = Installment(
        id=1,
        nome_fatura="X",
        cartao_id=1,
        mes_referencia="2026-01",
        valor_parcela=100.0 / 3.0,
        total_parcelas=3,
        parcelas_pagas=1,
    )
    assert inst.valor_total == 100.0
    sched = schedule_parcel_amounts(100.0, 3)
    assert inst.saldo_devedor == round(sum(sched[1:]), 2)
