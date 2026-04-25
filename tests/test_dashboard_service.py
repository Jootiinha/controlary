"""Testes de agregação do dashboard (sem UI)."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.services import accounts_service, dashboard_service

REF_MONTH = "2026-04"


def _seed_sample_data() -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta A', 1000)"
        )
        cur = conn.execute(
            """
            INSERT INTO payments (valor, descricao, data, conta_id, forma_pagamento)
            VALUES (50.0, 'Lançamento teste', ?, 1, 'Pix')
            """,
            (f"{REF_MONTH}-15",),
        )
        pid = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (1, ?, -50.0, 'pagamento', ?, ?)
            """,
            (
                f"{REF_MONTH}-15",
                accounts_service.transaction_key_payment(pid),
                "Lançamento teste",
            ),
        )
        conn.execute(
            """
            INSERT INTO income_sources (nome, valor_mensal, ativo, dia_recebimento)
            VALUES ('Salário', 5000.0, 1, 5)
            """
        )


def test_load_dashboard_totals_and_breakdown(test_db_path: Path) -> None:
    _seed_sample_data()
    data = dashboard_service.load(mes=REF_MONTH)

    assert data.mes_referencia == REF_MONTH
    assert data.total_gasto_mes == 50.0
    assert data.renda_mensal_total == 5000.0
    assert data.previsto_mes == 0.0
    assert data.saldo_projetado_fim_mes == 5950.0
    assert data.margem_apos_gasto == 4950.0
    assert data.gastos_por_conta == [("Conta A", 50.0)]
    assert data.gastos_por_forma == [("Pix", 50.0)]
    assert dashboard_service.previsto_mes_for(REF_MONTH) == data.previsto_mes


def test_total_gasto_mes_exclui_ajuste_livro_caixa(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta B', 2000)"
        )
        cur = conn.execute(
            """
            INSERT INTO payments (valor, descricao, data, conta_id, forma_pagamento)
            VALUES (30.0, 'Compra', ?, 1, 'Pix')
            """,
            (f"{REF_MONTH}-10",),
        )
        pid = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (1, ?, -30.0, 'pagamento', ?, 'Compra')
            """,
            (
                f"{REF_MONTH}-10",
                accounts_service.transaction_key_payment(pid),
            ),
        )
        conn.execute(
            """
            INSERT INTO account_transactions (
                account_id, data, valor, origem, transaction_key, descricao
            ) VALUES (1, ?, -200.0, 'ajuste', 'adjustment:z', 'Ajuste manual')
            """,
            (f"{REF_MONTH}-11",),
        )
    data = dashboard_service.load(mes=REF_MONTH)
    assert data.total_gasto_mes == 30.0


def test_load_empty_database(test_db_path: Path) -> None:
    data = dashboard_service.load(mes=REF_MONTH)

    assert data.mes_referencia == REF_MONTH
    assert data.total_gasto_mes == 0.0
    assert data.renda_mensal_total == 0.0
    assert data.gastos_por_conta == []
    assert data.gastos_por_forma == []


def test_dashboard_kpi_assinaturas_inclui_cartao_previsto_so_conta(test_db_path: Path) -> None:
    """KPI mostra todas as ativas; a parcela de assinaturas no previsto continua só em conta."""
    _seed_sample_data()
    with transaction() as conn:
        conn.execute("INSERT INTO cards (nome, account_id) VALUES ('Visa', 1)")
        conn.execute(
            """
            INSERT INTO subscriptions (
                nome, categoria, valor_mensal, dia_cobranca, forma_pagamento,
                conta_cartao, account_id, card_id, status
            ) VALUES ('Netflix conta', 'x', 10.0, 5, 'Débito', NULL, 1, NULL, 'ativa')
            """
        )
        conn.execute(
            """
            INSERT INTO subscriptions (
                nome, categoria, valor_mensal, dia_cobranca, forma_pagamento,
                conta_cartao, account_id, card_id, status
            ) VALUES ('Spotify cartão', 'x', 20.0, 10, 'Cartão', NULL, NULL, 1, 'ativa')
            """
        )

    data = dashboard_service.load(mes=REF_MONTH)

    assert data.assinaturas_ativas_valor == 10.0
    assert data.assinaturas_ativas_qtd == 1
    assert data.assinaturas_kpi_valor_mensal == 30.0
    assert data.assinaturas_kpi_qtd == 2
    assert data.assinaturas_kpi_em_conta_qtd == 1
    assert data.assinaturas_kpi_no_cartao_qtd == 1
    # previsto: fatura sugerida (20) + assinatura em conta (10); avulso já no livro não entra de novo
    assert data.previsto_faturas == 20.0
    assert data.previsto_mes == 30.0
