"""Cenários da auditoria do fluxo financeiro (parcelas, faturas, livro-caixa, rendas)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.models.income_source import IncomeSource
from app.models.installment import Installment
from app.services import (
    accounts_service,
    card_invoices_service,
    income_sources_service,
    installments_service,
    payments_service,
)


def test_parcela_cartao_entra_no_segundo_mes_sugerido(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 0)")
        conn.execute("INSERT INTO cards (nome, account_id) VALUES ('C1', 1)")
        row = conn.execute("SELECT id FROM categories ORDER BY id LIMIT 1").fetchone()
        cat_id = int(row["id"])
    iid = installments_service.create(
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
    assert card_invoices_service.suggested_total(1, "2026-01") == 100.0
    assert card_invoices_service.suggested_total(1, "2026-02") == 100.0
    assert card_invoices_service.suggested_total(1, "2026-03") == 100.0
    assert card_invoices_service.suggested_total(1, "2026-04") == 0.0
    inv = card_invoices_service.ensure_row_for_card_month(1, "2026-02")
    card_invoices_service.mark_paid(inv.id, 1, "2026-02-10")
    inst = installments_service.get(iid)
    assert inst is not None
    assert inst.parcelas_pagas == 1


def test_excluir_conta_bloqueada_com_movimento_livro(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('B', 100)")
        cur = conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (1, '2026-01-05', -10.0, 'ajuste', 'adjustment:x', 'x')
            """
        )
    with pytest.raises(ValueError, match="livro-caixa"):
        accounts_service.delete(1)


def test_renda_destrutiva_exige_confirmacao(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('C', 0)")
        conn.execute(
            """
            INSERT INTO income_sources (
                nome, valor_mensal, ativo, dia_recebimento, tipo, mes_referencia
            ) VALUES ('Bônus', 100.0, 1, 5, 'avulsa', '2026-03')
            """
        )
        sid = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    from app.services import income_months_service

    income_months_service.set_month_status(sid, "2026-03", True, valor_efetivo=100.0)
    with pytest.raises(income_sources_service.DestructiveIncomeUpdateError):
        income_sources_service.update(
            IncomeSource(
                id=sid,
                nome="Bônus",
                valor_mensal=100.0,
                ativo=True,
                dia_recebimento=5,
                account_id=1,
                tipo="avulsa",
                mes_referencia="2026-04",
            )
        )
    income_sources_service.update(
        IncomeSource(
            id=sid,
            nome="Bônus",
            valor_mensal=100.0,
            ativo=True,
            dia_recebimento=5,
            account_id=1,
            tipo="avulsa",
            mes_referencia="2026-04",
        ),
        confirm_destructive_prune=True,
    )


def test_reabrir_fatura_reverte_parcelas_pagas(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 0)")
        conn.execute("INSERT INTO cards (nome, account_id) VALUES ('C1', 1)")
        row = conn.execute("SELECT id FROM categories ORDER BY id LIMIT 1").fetchone()
        cat_id = int(row["id"])
    iid = installments_service.create(
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
    card_invoices_service.mark_paid(inv.id, 1, "2026-02-12")
    assert installments_service.get(iid).parcelas_pagas == 1
    card_invoices_service.set_status(inv.id, "aberta")
    assert installments_service.get(iid).parcelas_pagas == 0


def test_pagamento_cartao_para_conta_cria_livro(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO accounts (nome, saldo_inicial) VALUES ('A', 1000)")
        conn.execute("INSERT INTO cards (nome, account_id) VALUES ('V', 1)")
        row = conn.execute("SELECT id FROM categories ORDER BY id LIMIT 1").fetchone()
        cat_id = int(row["id"])
        cur = conn.execute(
            """
            INSERT INTO payments (
                valor, descricao, data, conta, conta_id, cartao_id, forma_pagamento, category_id
            ) VALUES (40.0, 'Loja', '2026-05-10', 'V', NULL, 1, 'Crédito', ?)
            """,
            (cat_id,),
        )
        pid = int(cur.lastrowid)
    p = payments_service.get(pid)
    assert p is not None
    p.conta_id = 1
    p.cartao_id = None
    p.conta = "A"
    payments_service.update(p)
    key = accounts_service.transaction_key_payment(pid)
    with transaction() as conn:
        row = conn.execute(
            "SELECT valor FROM account_transactions WHERE transaction_key = ?",
            (key,),
        ).fetchone()
    assert row is not None and float(row["valor"]) == -40.0
