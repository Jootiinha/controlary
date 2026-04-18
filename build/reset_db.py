"""Remove o banco SQLite do usuário (portável)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    home = Path(os.path.expanduser("~"))
    db = home / ".controle-financeiro" / "app.db"
    if db.is_file():
        db.unlink()
        print(f"Removido: {db}")
    else:
        print("Banco não encontrado (nada a fazer).")


if __name__ == "__main__":
    main()
    sys.exit(0)
