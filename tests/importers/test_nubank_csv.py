from __future__ import annotations

from pathlib import Path

from app.importers.banks.nubank_csv import parse_nubank_csv


def test_nubank_csv_basic(tmp_path: Path) -> None:
    csv_text = """date,title,amount
2024-03-10,Uber Trip,-12.50
2024-03-11,IFOOD,45.00
"""
    p = tmp_path / "n.csv"
    p.write_text(csv_text, encoding="utf-8")
    prev = parse_nubank_csv(p)
    assert prev.kind == "fatura"
    assert len(prev.transactions) == 2
    assert prev.transactions[0].valor == -12.5
    assert "Uber" in prev.transactions[0].descricao
