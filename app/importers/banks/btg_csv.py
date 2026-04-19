"""Extrato CSV BTG — ajuste conforme export real."""

from __future__ import annotations

from pathlib import Path

from app.importers.banks.generic_csv import parse_generic_csv_extrato


def parse_btg_csv(path: Path):
    return parse_generic_csv_extrato(path, banco_hint="BTG")
