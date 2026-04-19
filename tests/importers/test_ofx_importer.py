from __future__ import annotations

from pathlib import Path

from app.importers.ofx_importer import parse_ofx_file


def test_parse_ofx_stmttrn(tmp_path: Path) -> None:
    ofx = """OFXHEADER:100
DATA:OFXSGML
<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20240115120000[-3:BRT]
<TRNAMT>-50.25
<FITID>abc123
<NAME>Teste Mercado
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""
    p = tmp_path / "t.ofx"
    p.write_text(ofx, encoding="utf-8")
    prev = parse_ofx_file(p, "extrato")
    assert len(prev.transactions) == 1
    t = prev.transactions[0]
    assert t.valor == -50.25
    assert "Mercado" in t.descricao
    assert t.external_id.startswith("ofx:")
