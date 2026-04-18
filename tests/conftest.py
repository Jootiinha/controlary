"""Fixtures partilhados: BD SQLite isolada por teste via CONTROLE_FINANCEIRO_DB."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.database.migrations import run_migrations


@pytest.fixture
def test_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Aponta o app para um ficheiro SQLite temporário e aplica migrações."""
    db = tmp_path / "test.db"
    monkeypatch.setenv("CONTROLE_FINANCEIRO_DB", str(db))
    run_migrations()
    return db
