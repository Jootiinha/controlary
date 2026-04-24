"""Competência mensal YYYY-MM como value object."""
from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from typing import Iterator

_RE_YM = re.compile(r"^(\d{4})-(\d{1,2})$")


@dataclass(frozen=True)
class MesAno:
    ano: int
    mes: int

    def __post_init__(self) -> None:
        if not (1 <= self.mes <= 12):
            raise ValueError(f"Mês inválido: {self.mes}")

    @classmethod
    def from_str(cls, s: str) -> MesAno:
        s = (s or "").strip()
        m = _RE_YM.match(s)
        if not m:
            raise ValueError(f"Competência inválida (use YYYY-MM): {s!r}")
        y, mo = int(m.group(1)), int(m.group(2))
        return cls(y, mo)

    @classmethod
    def try_from_str(cls, s: str) -> MesAno | None:
        try:
            return cls.from_str(s)
        except ValueError:
            return None

    def __str__(self) -> str:
        return f"{self.ano:04d}-{self.mes:02d}"

    def last_day(self) -> int:
        return monthrange(self.ano, self.mes)[1]

    def with_day(self, dia: int) -> date:
        ultimo = self.last_day()
        return date(self.ano, self.mes, min(int(dia), ultimo))

    def next(self) -> MesAno:
        if self.mes == 12:
            return MesAno(self.ano + 1, 1)
        return MesAno(self.ano, self.mes + 1)

    def previous(self) -> MesAno:
        if self.mes == 1:
            return MesAno(self.ano - 1, 12)
        return MesAno(self.ano, self.mes - 1)

    def iter_until(self, other: MesAno) -> Iterator[MesAno]:
        cur = self
        end_key = (other.ano, other.mes)
        while (cur.ano, cur.mes) <= end_key:
            yield cur
            cur = cur.next()
