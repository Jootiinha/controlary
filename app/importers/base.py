from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

ImportKind = Literal["fatura", "extrato"]


@dataclass(frozen=True)
class ParsedTransaction:
    data: date
    valor: float
    descricao: str
    external_id: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportPreview:
    kind: ImportKind
    banco_hint: str | None
    ano_mes_hint: str | None
    moeda: str
    transactions: list[ParsedTransaction]
    source_label: str
