from __future__ import annotations

import csv
import hashlib
from datetime import date
from pathlib import Path

from app.importers.base import ImportKind, ImportPreview, ParsedTransaction


def _parse_date(cell: str) -> date | None:
    cell = cell.strip()
    if not cell:
        return None
    part = cell.split(" ")[0].split("T")[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(part, fmt).date()
        except ValueError:
            continue
    return None


def _ext_id(d: date, desc: str, amt: float, row_idx: int) -> str:
    base = f"nubank|{d.isoformat()}|{amt:.2f}|{desc}|{row_idx}"
    return f"csv:sha1:{hashlib.sha1(base.encode('utf-8')).hexdigest()}"


def parse_nubank_csv(path: Path) -> ImportPreview:
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    lines = raw_text.splitlines()
    if not lines:
        return ImportPreview(
            kind="fatura",
            banco_hint="Nubank",
            ano_mes_hint=None,
            moeda="BRL",
            transactions=[],
            source_label=path.name,
        )
    sample = raw_text[:4096]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    field_map = {k.lower().strip(): k for k in (reader.fieldnames or [])}

    def col(*names: str) -> str | None:
        for n in names:
            k = field_map.get(n.lower())
            if k:
                return k
        return None

    c_date = col("date", "data")
    c_title = col("title", "titulo", "título", "description", "descricao", "descrição")
    c_amt = col("amount", "valor")
    txs: list[ParsedTransaction] = []
    if not c_date or not c_amt:
        return ImportPreview(
            kind="fatura",
            banco_hint="Nubank",
            ano_mes_hint=None,
            moeda="BRL",
            transactions=[],
            source_label=path.name,
        )

    for idx, row in enumerate(reader):
        ds = str(row.get(c_date, "")).strip()
        d = _parse_date(ds)
        if d is None:
            continue
        title = ""
        if c_title:
            title = str(row.get(c_title, "")).strip()
        try:
            amt_s = str(row.get(c_amt, "")).strip().replace(",", ".")
            amt = float(amt_s)
        except ValueError:
            continue
        desc = title or "(sem descrição)"
        ext = _ext_id(d, desc, amt, idx)
        txs.append(
            ParsedTransaction(
                data=d,
                valor=amt,
                descricao=desc[:500],
                external_id=ext,
                raw=dict(row),
            )
        )

    txs.sort(key=lambda t: (t.data, t.external_id))
    ano_mes = None
    if txs:
        d0 = txs[0].data
        ano_mes = f"{d0.year:04d}-{d0.month:02d}"

    return ImportPreview(
        kind="fatura",
        banco_hint="Nubank",
        ano_mes_hint=ano_mes,
        moeda="BRL",
        transactions=txs,
        source_label=path.name,
    )
