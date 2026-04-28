from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class Toast(QFrame):
    def __init__(
        self,
        parent: QWidget,
        message: str,
        *,
        action_label: str | None = None,
        on_action: Callable[[], None] | None = None,
        duration_ms: int = 4500,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        lbl = QLabel(message)
        lbl.setObjectName("ToastMessage")
        lbl.setWordWrap(True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.addWidget(lbl, 1)
        if action_label and on_action:
            btn = QPushButton(action_label)
            btn.setObjectName("ToastAction")
            btn.clicked.connect(lambda: (on_action(), self.close()))
            lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignRight)
        QTimer.singleShot(duration_ms, self.close)
