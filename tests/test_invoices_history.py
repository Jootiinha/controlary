"""history_by_card: filtro de status e agrupamento por cartão."""
from __future__ import annotations

from pathlib import Path

from app.database.connection import transaction
from app.services import card_invoices_service


def test_history_by_card_filters_aberta_and_groups(test_db_path: Path) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO cards (nome) VALUES ('Cartão A')")
        conn.execute("INSERT INTO cards (nome) VALUES ('Cartão B')")
        conn.execute(
            """
            INSERT INTO card_invoices (cartao_id, ano_mes, valor_total, status)
            VALUES
                (1, '2025-01', 100.0, 'paga'),
                (1, '2025-02', 50.0, 'fechada'),
                (1, '2025-03', 999.0, 'aberta'),
                (2, '2025-02', 200.0, 'paga')
            """
        )

    got = card_invoices_service.history_by_card("2025-01", "2025-03")

    assert 1 in got and 2 in got
    assert [(ym, v) for ym, v in got[1]] == [
        ("2025-01", 100.0),
        ("2025-02", 50.0),
    ]
    assert got[2] == [("2025-02", 200.0)]
    assert all("2025-03" not in ym for lst in got.values() for ym, _ in lst)
