"""Diálogo de revisão antes de confirmar importação de extrato/fatura."""
from __future__ import annotations

from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.importers.base import ImportPreview
from app.services import import_rules_service, import_service
from app.services.import_service import EnrichedRow
from app.ui.widgets.category_picker import CategoryPicker
from app.utils.formatting import format_currency


class ImportReviewDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        preview: ImportPreview,
        enriched: list[EnrichedRow],
        mode: str,
        extra_label: str = "",
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self._enriched = enriched
        self._memorize = QCheckBox(
            "Ao mudar categoria, perguntar se deseja memorizar regra (contém texto)"
        )
        self._memorize.setChecked(True)
        self._asked_memo: set[str] = set()

        title = (
            "Revisar importação — extrato"
            if mode == "extrato"
            else "Revisar importação — fatura"
        )
        self.setWindowTitle(title)
        self.resize(920, 520)

        bh = preview.banco_hint or "—"
        am = preview.ano_mes_hint or "—"
        head = QLabel(
            f"Arquivo: {preview.source_label} · Banco (detecção): {bh} · "
            f"Período sugerido: {am} · Linhas: {len(enriched)}{extra_label}"
        )
        head.setWordWrap(True)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filtrar por descrição…")
        self._search.textChanged.connect(self._apply_filter)

        self._tbl = QTableWidget(len(enriched), 6)
        self._tbl.setHorizontalHeaderLabels(
            ["✓", "Data", "Descrição", "Valor", "Categoria", "Estado"]
        )
        self._tbl.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._tbl.setColumnWidth(0, 36)
        self._tbl.setColumnWidth(1, 100)
        self._tbl.setColumnWidth(3, 120)

        self._pickers: list[CategoryPicker] = []
        self._checks: list[QCheckBox] = []
        self._desc_edits: list[QLineEdit] = []

        for i, er in enumerate(enriched):
            tx = er.transaction
            chk = QCheckBox()
            chk.setChecked(not er.already_imported)
            if er.already_imported:
                chk.setEnabled(False)
            chk.stateChanged.connect(self._refresh_total)
            self._checks.append(chk)

            self._tbl.setItem(i, 1, QTableWidgetItem(tx.data.isoformat()))
            ed = QLineEdit(tx.descricao)
            self._desc_edits.append(ed)
            self._tbl.setCellWidget(i, 2, ed)

            amt = tx.valor
            sign = "−" if amt < 0 else "+"
            it_val = QTableWidgetItem(f"{sign} {format_currency(abs(amt))}")
            it_val.setTextAlignment(
                int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            )
            self._tbl.setItem(i, 3, it_val)

            pk = CategoryPicker(self, allow_empty=False)
            cid = er.suggested_category_id
            if cid is not None:
                pk.set_category_id(cid)
            pk.category_changed.connect(partial(self._on_category_changed, i, pk))
            self._pickers.append(pk)
            self._tbl.setCellWidget(i, 4, pk)

            st = "Já importado" if er.already_imported else "Novo"
            it_st = QTableWidgetItem(st)
            if er.already_imported:
                it_st.setForeground(Qt.GlobalColor.gray)
            self._tbl.setItem(i, 5, it_st)

            cw = QWidget()
            hl = QHBoxLayout(cw)
            hl.setContentsMargins(4, 0, 4, 0)
            hl.addWidget(chk)
            self._tbl.setCellWidget(i, 0, cw)

        btn_all = QPushButton("Marcar todos")
        btn_none = QPushButton("Desmarcar todos")
        btn_all.clicked.connect(lambda: self._set_all(True))
        btn_none.clicked.connect(lambda: self._set_all(False))
        row_btns = QHBoxLayout()
        row_btns.addWidget(btn_all)
        row_btns.addWidget(btn_none)
        row_btns.addStretch()

        self._lbl_total = QLabel()
        self._lbl_total.setObjectName("PageSubtitle")

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(self._try_accept)
        bb.rejected.connect(self.reject)
        ok_btn = bb.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText("Confirmar importação")

        lay = QVBoxLayout(self)
        lay.addWidget(head)
        lay.addLayout(row_btns)
        lay.addWidget(self._search)
        lay.addWidget(self._tbl, 1)
        lay.addWidget(self._lbl_total)
        lay.addWidget(self._memorize)
        lay.addWidget(bb)
        self._refresh_total()

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self._tbl.rowCount()):
            ed = self._desc_edits[i]
            match = not needle or needle in ed.text().lower()
            self._tbl.setRowHidden(i, not match)

    def _set_all(self, checked: bool) -> None:
        for chk in self._checks:
            if chk.isEnabled():
                chk.setChecked(checked)
        self._refresh_total()

    def _on_category_changed(self, row: int, picker: CategoryPicker) -> None:
        if not self._memorize.isChecked():
            return
        cid = picker.current_category_id()
        if cid is None:
            return
        desc = self._desc_edits[row].text().strip()
        if len(desc) < 3:
            return
        key = f"{row}:{cid}"
        if key in self._asked_memo:
            return
        token = desc[:48].strip()
        if len(token) < 3:
            return
        self._asked_memo.add(key)
        r = QMessageBox.question(
            self,
            "Memorizar regra",
            f"Sempre que a descrição contiver «{token}», usar esta categoria?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if r == QMessageBox.StandardButton.Yes:
            import_rules_service.insert_rule(token, "contains", cid, prioridade=10)

    def _refresh_total(self) -> None:
        total = 0.0
        for i, er in enumerate(self._enriched):
            if not self._checks[i].isChecked():
                continue
            v = er.transaction.valor
            total += abs(v)
        self._lbl_total.setText(
            f"Total selecionado (soma dos valores absolutos): {format_currency(total)}"
        )

    def _try_accept(self) -> None:
        if not self.build_commit_lines():
            QMessageBox.warning(
                self,
                "Importar",
                "Selecione ao menos uma linha nova (não importada anteriormente).",
            )
            return
        self.accept()

    def build_commit_lines(
        self,
    ) -> list[tuple]:
        out: list[tuple] = []
        for i, er in enumerate(self._enriched):
            if not self._checks[i].isChecked() or er.already_imported:
                continue
            tx = er.transaction
            desc = self._desc_edits[i].text().strip() or tx.descricao
            cid = self._pickers[i].current_category_id()
            out.append((tx, cid, desc))
        return out


def run_import_extrato_dialog(parent: QWidget | None, account_id: int, account_nome: str) -> bool:
    from PySide6.QtWidgets import QFileDialog

    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Importar extrato",
        "",
        "Extratos (*.ofx *.qfx *.csv *.xlsx *.xlsm);;Todos (*.*)",
    )
    if not path:
        return False
    try:
        preview, enriched = import_service.preview_file(path, "extrato")
    except Exception as e:
        QMessageBox.warning(parent, "Importar", str(e))
        return False
    if not enriched:
        QMessageBox.information(
            parent, "Importar", "Nenhuma transação encontrada no arquivo."
        )
        return False
    dlg = ImportReviewDialog(
        parent,
        preview,
        enriched,
        "extrato",
        f" · Conta: {account_nome}",
    )
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return False
    lines = dlg.build_commit_lines()
    if not lines:
        return False
    try:
        import_service.commit_extrato(
            account_id,
            Path(path).name,
            preview.banco_hint,
            lines,
        )
    except Exception as e:
        QMessageBox.warning(parent, "Importar", str(e))
        return False
    QMessageBox.information(parent, "Importar", "Extrato importado com sucesso.")
    return True


def run_import_fatura_dialog(
    parent: QWidget | None,
    cartao_id: int,
    cartao_nome: str,
    ano_mes: str,
) -> bool:
    from PySide6.QtWidgets import QFileDialog

    path, _ = QFileDialog.getOpenFileName(
        parent,
        "Importar fatura",
        "",
        "Faturas (*.csv *.ofx *.qfx *.xlsx *.xlsm);;Todos (*.*)",
    )
    if not path:
        return False
    try:
        preview, enriched = import_service.preview_file(path, "fatura")
    except Exception as e:
        QMessageBox.warning(parent, "Importar", str(e))
        return False
    if not enriched:
        QMessageBox.information(
            parent, "Importar", "Nenhuma transação encontrada no arquivo."
        )
        return False
    dlg = ImportReviewDialog(
        parent,
        preview,
        enriched,
        "fatura",
        f" · Cartão: {cartao_nome} · Competência: {ano_mes}",
    )
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return False
    lines = dlg.build_commit_lines()
    if not lines:
        return False
    try:
        import_service.commit_fatura(
            cartao_id,
            ano_mes,
            Path(path).name,
            preview.banco_hint,
            lines,
        )
    except Exception as e:
        QMessageBox.warning(parent, "Importar", str(e))
        return False
    QMessageBox.information(parent, "Importar", "Fatura importada com sucesso.")
    return True
