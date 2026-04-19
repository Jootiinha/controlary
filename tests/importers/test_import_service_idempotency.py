from __future__ import annotations

from pathlib import Path

import pytest

from app.database.connection import transaction
from app.database.migrations import run_migrations
from app.services import categories_service, import_service
from app.importers.ofx_importer import parse_ofx_file


@pytest.fixture()
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "t.db"
    monkeypatch.setenv("CONTROLE_FINANCEIRO_DB", str(db))
    monkeypatch.setattr("app.utils.paths.database_path", lambda: db)
    run_migrations()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO accounts (nome, saldo_inicial) VALUES ('Conta T', 1000)"
        )
        conn.execute(
            """
            INSERT INTO cards (nome, account_id, dia_pagamento_fatura)
            VALUES ('Cartão T', 1, 10)
            """
        )
    return db


def test_external_id_skips_duplicate_in_preview(isolated_db: Path) -> None:
    ofx = """OFXHEADER:100
<OFX>
<STMTTRN>
<DTPOSTED>20240201120000
<TRNAMT>-10.00
<FITID>dup1
<NAME>X
</STMTTRN>
</OFX>
"""
    p = isolated_db.parent / "x.ofx"
    p.write_text(ofx, encoding="utf-8")
    prev = parse_ofx_file(p, "extrato")
    assert len(prev.transactions) == 1
    ext = prev.transactions[0].external_id
    cid = categories_service.default_category_id()
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO payments (
                valor, descricao, data, conta, conta_id, cartao_id,
                forma_pagamento, category_id, external_id
            ) VALUES (10, 'x', '2024-02-01', 'Conta T', 1, NULL, 'Importação', ?, ?)
            """,
            (cid, ext),
        )
    _out, enriched = import_service.preview_file(p, "extrato")
    assert len(enriched) == 1
    assert enriched[0].already_imported is True
