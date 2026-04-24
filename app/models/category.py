from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    id: Optional[int]
    nome: str
    tipo_sugerido: Optional[str] = None
    cor: Optional[str] = None
    ativo: bool = True

    @classmethod
    def unknown(cls, label: str = "—") -> "Category":
        return cls(
            id=None,
            nome=label,
            tipo_sugerido=None,
            cor=None,
            ativo=False,
        )

    @classmethod
    def from_row(cls, row) -> "Category":
        keys = list(row.keys())
        ativo = bool(row["ativo"]) if "ativo" in keys else True
        return cls(
            id=row["id"],
            nome=row["nome"],
            tipo_sugerido=row["tipo_sugerido"] if "tipo_sugerido" in keys else None,
            cor=row["cor"] if "cor" in keys else None,
            ativo=ativo,
        )
