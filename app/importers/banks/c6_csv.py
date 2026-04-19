"""Extrato CSV C6 Bank — ajuste conforme export real."""

from __future__ import annotations

from pathlib import Path

from app.importers.banks.generic_csv import parse_generic_csv_extrato


def parse_c6_csv(path: Path):
    return parse_generic_csv_extrato(path, banco_hint="C6")
