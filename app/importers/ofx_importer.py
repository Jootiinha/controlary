from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path
from typing import Any

from app.importers.base import ImportKind, ImportPreview, ParsedTransaction

_TAG_RE = re.compile(r"<([A-Z0-9.]+)>([^<\r\n]*)", re.IGNORECASE)


def _parse_ofx_tags(block: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in _TAG_RE.finditer(block):
        tag = m.group(1).upper().strip()
        val = (m.group(2) or "").strip()
        if tag and val:
            out[tag] = val
    return out


def _dtposted_to_date(s: str) -> date | None:
    s = s.strip()
    if len(s) >= 8 and s[:8].isdigit():
        y, mo, d = int(s[0:4]), int(s[4:6]), int(s[6:8])
        try:
            return date(y, mo, d)
        except ValueError:
            return None
    return None


def _fitid_or_hash(tags: dict[str, str], desc: str, amt: float, d: date) -> str:
    fid = tags.get("FITID") or tags.get("REFNUM")
    if fid:
        return f"ofx:{fid}"
    base = f"{d.isoformat()}|{amt:.2f}|{desc}"
    return f"ofx:sha1:{hashlib.sha1(base.encode('utf-8')).hexdigest()}"


def parse_ofx_file(path: Path, kind_hint: ImportKind | None) -> ImportPreview:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        text = path.read_text(encoding="latin-1", errors="replace")

    banco_hint = None
    m_org = re.search(r"<ORG>([^<\r\n]+)", text, re.I)
    if m_org:
        banco_hint = m_org.group(1).strip()
    m_fid = re.search(r"<FID>([^<\r\n]+)", text, re.I)
    if m_fid and not banco_hint:
        banco_hint = m_fid.group(1).strip()

    blocks = re.split(r"(?i)<STMTTRN\s*>", text)
    txs: list[ParsedTransaction] = []
    for block in blocks[1:]:
        end = block.find("</STMTTRN>")
        chunk = block[:end] if end >= 0 else block
        tags = _parse_ofx_tags(chunk)
        trnamt = tags.get("TRNAMT")
        if trnamt is None:
            continue
        try:
            amt = float(trnamt.replace(",", "."))
        except ValueError:
            continue
        dt_raw = tags.get("DTPOSTED") or tags.get("DTUSER") or tags.get("DTSERVER")
        if not dt_raw:
            continue
        d = _dtposted_to_date(dt_raw)
        if d is None:
            continue
        name = (tags.get("NAME") or "").strip()
        memo = (tags.get("MEMO") or "").strip()
        desc = name if name else memo
        if name and memo and memo.lower() != name.lower():
            desc = f"{name} — {memo}"
        if not desc:
            desc = "(sem descrição)"
        ext = _fitid_or_hash(tags, desc, amt, d)
        raw: dict[str, Any] = dict(tags)
        txs.append(
            ParsedTransaction(
                data=d,
                valor=amt,
                descricao=desc[:500],
                external_id=ext,
                raw=raw,
            )
        )

    txs.sort(key=lambda t: (t.data, t.external_id))
    ano_mes: str | None = None
    if txs:
        d0 = txs[0].data
        ano_mes = f"{d0.year:04d}-{d0.month:02d}"

    kind: ImportKind = kind_hint or "extrato"
    if kind == "extrato" and not txs:
        kind = "extrato"

    return ImportPreview(
        kind=kind,
        banco_hint=banco_hint,
        ano_mes_hint=ano_mes,
        moeda="BRL",
        transactions=txs,
        source_label=path.name,
    )
