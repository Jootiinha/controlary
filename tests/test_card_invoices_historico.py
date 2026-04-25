"""Faturas históricas: registo sem livro-caixa e sem incremento de parcelas."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.models.installment import Installment
from app.services import (
    accounts_service,
    card_invoices_service,
    installments_service,
)


def test_mark_paid_historico_nao_gera_livro_nem_parcela(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 0)")
        conn.execute("INSERT INTO cards (nome, account_id) VALUES ('C1', 1)")
        row = conn.execute("SELECT id FROM categories ORDER BY id LIMIT 1").fetchone()
        cat_id = int(row["id"])
    iid_inst = installments_service.create(
        Installment(
            id=None,
            nome_fatura="Compra",
            cartao_id=1,
            mes_referencia="2026-01",
            valor_parcela=100.0,
            total_parcelas=3,
            parcelas_pagas=0,
            category_id=cat_id,
        )
    )
    inv = card_invoices_service.ensure_row_for_card_month(1, "2026-02")
    card_invoices_service.mark_paid_historico(inv.id, "2026-02-10")
    key = accounts_service.transaction_key_invoice(inv.id)
    with transaction() as conn:
        n = conn.execute(
            "SELECT COUNT(*) AS c FROM account_transactions WHERE transaction_key = ?",
            (key,),
        ).fetchone()
    assert int(n["c"] or 0) == 0
    assert installments_service.get(iid_inst).parcelas_pagas == 0
    inv2 = card_invoices_service.get(1, "2026-02")
    assert inv2 is not None
    assert inv2.status == "paga"
    assert inv2.historico is True


def test_reabrir_fatura_historica_nao_toca_parcela(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 0)")
        conn.execute("INSERT INTO cards (nome, account_id) VALUES ('C1', 1)")
        row = conn.execute("SELECT id FROM categories ORDER BY id LIMIT 1").fetchone()
        cat_id = int(row["id"])
    iid_inst = installments_service.create(
        Installment(
            id=None,
            nome_fatura="X",
            cartao_id=1,
            mes_referencia="2026-01",
            valor_parcela=50.0,
            total_parcelas=2,
            parcelas_pagas=0,
            category_id=cat_id,
        )
    )
    inv = card_invoices_service.ensure_row_for_card_month(1, "2026-02")
    card_invoices_service.mark_paid_historico(inv.id, "2026-02-12")
    assert installments_service.get(iid_inst).parcelas_pagas == 0
    card_invoices_service.set_status(inv.id, "aberta")
    assert installments_service.get(iid_inst).parcelas_pagas == 0
    inv3 = card_invoices_service.get_by_id(inv.id)
    assert inv3 is not None
    assert inv3.historico is False
