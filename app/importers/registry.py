from __future__ import annotations

import tempfile
from pathlib import Path

from app.importers.base import ImportKind, ImportPreview
from app.importers.banks.generic_csv import parse_generic_csv_extrato, sniff_csv_kind
from app.importers.banks.nubank_csv import parse_nubank_csv
from app.importers.ofx_importer import parse_ofx_file


def detect_and_parse(path: Path, kind: ImportKind | None) -> ImportPreview:
    p = path.expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(str(p))
    suf = p.suffix.lower()
    if suf in (".ofx", ".qfx"):
        return parse_ofx_file(p, kind)
    if suf == ".csv":
        sniff = sniff_csv_kind(p)
        if sniff == "nubank_like" and kind != "extrato":
            return parse_nubank_csv(p)
        if sniff == "extrato_generico" or kind == "extrato":
            return parse_generic_csv_extrato(p, banco_hint=None)
        if sniff == "nubank_like":
            return parse_nubank_csv(p)
        return parse_generic_csv_extrato(p, banco_hint=None)
    if suf in (".xlsx", ".xlsm"):
        return _parse_xlsx(p, kind)
    raise ValueError(f"Formato não suportado: {suf}. Use OFX, CSV ou XLSX.")


def _parse_xlsx(path: Path, kind: ImportKind | None) -> ImportPreview:
    try:
        import openpyxl  # type: ignore[import-untyped]
    except ImportError as e:
        raise ValueError(
            "Instale openpyxl para importar planilhas Excel (ex.: poetry add openpyxl)."
        ) from e
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    lines: list[str] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i > 8000:
            break
        cells = [("" if c is None else str(c)).strip() for c in row]
        if not any(cells):
            continue
        lines.append(";".join(cells))
    wb.close()
    text = "\n".join(lines)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        delete=False,
        encoding="utf-8",
        newline="",
    ) as tf:
        tf.write(text)
        tmp_path = Path(tf.name)
    try:
        sniff = sniff_csv_kind(tmp_path)
        if sniff == "nubank_like" and kind != "extrato":
            prev = parse_nubank_csv(tmp_path)
        else:
            prev = parse_generic_csv_extrato(tmp_path, banco_hint=None)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
    return ImportPreview(
        kind=prev.kind,
        banco_hint=prev.banco_hint,
        ano_mes_hint=prev.ano_mes_hint,
        moeda=prev.moeda,
        transactions=prev.transactions,
        source_label=path.name,
    )
