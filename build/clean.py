"""Remove artefatos de build e caches (portável)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    for name in ("dist",):
        p = ROOT / name
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    bb = ROOT / "build" / "build"
    if bb.is_dir():
        shutil.rmtree(bb, ignore_errors=True)
    for p in ROOT.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    for p in ROOT.rglob("*.pyc"):
        try:
            p.unlink()
        except OSError:
            pass
    print("Limpeza concluída.")


if __name__ == "__main__":
    main()
    sys.exit(0)
