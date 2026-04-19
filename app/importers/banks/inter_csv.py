"""Extrato CSV Banco Inter — ajuste conforme export real."""

from __future__ import annotations

from pathlib import Path

from app.importers.banks.generic_csv import parse_generic_csv_extrato


def parse_inter_csv(path: Path):
    return parse_generic_csv_extrato(path, banco_hint="Inter")
