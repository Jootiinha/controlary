"""Resolução de caminhos em desenvolvimento e em builds empacotadas (PyInstaller)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_path(relative: str) -> str:
    """Retorna o caminho absoluto de um recurso incluso no bundle.

    Funciona tanto rodando via ``python main.py`` quanto via executável gerado
    pelo PyInstaller (que extrai recursos em ``sys._MEIPASS``).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = Path(__file__).resolve().parents[2]
    return str(Path(base) / relative)


def user_data_dir() -> Path:
    """Diretório persistente do usuário para o banco SQLite e afins."""
    home = Path.home()
    directory = home / ".controle-financeiro"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def database_path() -> Path:
    override = os.environ.get("CONTROLE_FINANCEIRO_DB")
    if override:
        path = Path(override).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return user_data_dir() / "app.db"
