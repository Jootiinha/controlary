"""Base para diálogos de formulário (add/edit)."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class FormDialog(QDialog):
    """Diálogo com um QFormLayout e botões OK/Cancelar."""

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("FormDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(440)

        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)
        self.form.setContentsMargins(8, 8, 8, 8)
        self.form.setHorizontalSpacing(12)
        self.form.setVerticalSpacing(10)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttons.button(QDialogButtonBox.Ok).setText("Salvar")
        self.buttons.button(QDialogButtonBox.Ok).setObjectName("PrimaryButton")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.addLayout(self.form)
        outer.addWidget(self.buttons)

    def add_section(self, title: str) -> None:
        lab = QLabel(title)
        lab.setObjectName("FormSectionTitle")
        lab.setStyleSheet("font-weight: 600; margin-top: 8px;")
        self.form.addRow(lab)

    def _on_accept(self) -> None:
        ok, err = self.validate()
        if not ok:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Validação", err or "Verifique os campos")
            return
        self.accept()

    def validate(self) -> tuple[bool, str | None]:
        return True, None
