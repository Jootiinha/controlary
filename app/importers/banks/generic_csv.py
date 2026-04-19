from __future__ import annotations

import csv
import hashlib
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.importers.base import ImportKind, ImportPreview, ParsedTransaction


def _looks_like_brazilian_statement(header_line: str) -> bool:
    h = header_line.lower()
    keys = (
        "data",
        "hist",
        "descri",
        "valor",
        "lançamento",
        "lancamento",
        "credito",
        "crédito",
        "debito",
        "débito",
        "saldo",
    )
    return any(k in h for k in keys)


def _parse_float_br(s: str) -> float | None:
    s = s.strip().replace("R$", "").replace(" ", "")
    if not s or s == "-":
        return None
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    sign = -1.0 if s.startswith("-") else 1.0
    s = s.lstrip("-").strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        v = float(s) * sign
        return -v if neg else v
    except ValueError:
        return None


def _parse_date_cell(s: str) -> date | None:
    s = s.strip().split(" ")[0]
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _ext(row_idx: int, d: date, desc: str, amt: float) -> str:
    base = f"csvgen|{d.isoformat()}|{amt:.2f}|{desc}|{row_idx}"
    return f"csv:sha1:{hashlib.sha1(base.encode('utf-8')).hexdigest()}"


def parse_generic_csv_extrato(path: Path, banco_hint: str | None) -> ImportPreview:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    if len(lines) < 2:
        return ImportPreview(
            kind="extrato",
            banco_hint=banco_hint,
            ano_mes_hint=None,
            moeda="BRL",
            transactions=[],
            source_label=path.name,
        )
    delimiter = ";" if lines[0].count(";") > lines[0].count(",") else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    names = reader.fieldnames or []
    lower = {n.lower().strip(): n for n in names}

    def pick(*candidates: str) -> str | None:
        for c in candidates:
            for k, v in lower.items():
                if c in k:
                    return v
        return None

    c_data = pick("data", "date")
    c_desc = pick("hist", "descri", "detalhe", "lancamento", "lançamento", "memo")
    c_val = pick("valor")

    txs: list[ParsedTransaction] = []
    if c_data and c_desc and c_val:
        for idx, row in enumerate(reader):
            ds = str(row.get(c_data, "")).strip()
            d = _parse_date_cell(ds)
            if d is None:
                continue
            desc = str(row.get(c_desc, "")).strip() or "(sem descrição)"
            vf = _parse_float_br(str(row.get(c_val, "")))
            if vf is None:
                continue
            txs.append(
                ParsedTransaction(
                    data=d,
                    valor=vf,
                    descricao=desc[:500],
                    external_id=_ext(idx, d, desc, vf),
                    raw=dict(row),
                )
            )

    txs.sort(key=lambda t: (t.data, t.external_id))
    ano_mes = None
    if txs:
        d0 = txs[0].data
        ano_mes = f"{d0.year:04d}-{d0.month:02d}"

    return ImportPreview(
        kind="extrato",
        banco_hint=banco_hint,
        ano_mes_hint=ano_mes,
        moeda="BRL",
        transactions=txs,
        source_label=path.name,
    )


def sniff_csv_kind(path: Path) -> str | None:
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except IndexError:
        return None
    low = first.lower()
    if "date" in low and ("amount" in low or "valor" in low):
        return "nubank_like"
    if _looks_like_brazilian_statement(first):
        return "extrato_generico"
    return None
