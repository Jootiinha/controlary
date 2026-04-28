"""Lista recente do livro-caixa (todas as contas)."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from app.services import accounts_service
from app.ui.widgets.readonly_table import ReadOnlyTable
from app.utils.formatting import format_currency, format_date_br


class LedgerView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        lbl = QLabel(
            "Últimas movimentações registradas no livro-caixa (ajustes, transferências, "
            "débitos em conta, etc.)."
        )
        lbl.setObjectName("PageSubtitle")
        lbl.setWordWrap(True)
        self._tbl = ReadOnlyTable(
            ["Data", "Conta", "Origem", "Descrição", "Valor"],
            min_height=320,
            size_policy=(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            ),
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)
        lay.addWidget(lbl)
        lay.addWidget(self._tbl, 1)

    def reload(self) -> None:
        rows_data = accounts_service.list_ledger_rows(500)
        if not rows_data:
            self._tbl.set_rows(
                [],
                empty_message="Nenhuma movimentação no livro-caixa ainda.",
            )
            return
        rows: list[list[str]] = []
        sort_keys: list[list[object]] = []
        for r in rows_data:
            desc = (r.get("descricao") or "") or ""
            if not isinstance(desc, str):
                desc = str(desc)
            val = float(r["valor"])
            rows.append([
                format_date_br(str(r["data"])),
                str(r["conta_nome"]),
                str(r["origem"]),
                desc,
                format_currency(val),
            ])
            sort_keys.append([
                str(r["data"]),
                str(r["conta_nome"]).casefold(),
                str(r["origem"]).casefold(),
                desc.casefold(),
                val,
            ])
        self._tbl.set_rows(rows, sort_keys=sort_keys)
