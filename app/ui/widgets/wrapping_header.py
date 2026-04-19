"""Cabeçalho de tabela com quebra de linha quando a coluna é estreita."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QHeaderView, QStyle, QStyleOptionHeader


class WrappingHeaderView(QHeaderView):
    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setSectionsClickable(True)
        self.setHighlightSections(False)
        self.setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.sectionResized.connect(self._on_section_resized)
        if parent is not None:
            parent.installEventFilter(self)

    def _on_section_resized(self, *_args) -> None:
        self.updateGeometry()
        self.viewport().update()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.parent() and event.type() == QEvent.Type.Resize:
            self.updateGeometry()
        return super().eventFilter(watched, event)

    def _header_text_height(self) -> int:
        model = self.model()
        if model is None:
            return 32
        h_min = 32
        for i in range(self.count()):
            if self.isSectionHidden(i):
                continue
            w = self.sectionSize(i)
            raw = model.headerData(
                i,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            text = str(raw) if raw is not None else ""
            br = self.fontMetrics().boundingRect(
                0,
                0,
                max(w - 12, 1),
                10_000,
                int(Qt.AlignmentFlag.AlignCenter | Qt.TextWordWrap),
                text,
            )
            h_min = max(h_min, br.height() + 12)
        return h_min

    def sizeHint(self) -> QSize:  # noqa: N802
        sh = super().sizeHint()
        return QSize(sh.width(), max(sh.height(), self._header_text_height()))

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        mh = super().minimumSizeHint()
        return QSize(mh.width(), max(mh.height(), self._header_text_height()))

    def paintSection(self, painter: QPainter, rect, logical_index: int) -> None:
        opt = QStyleOptionHeader()
        self.initStyleOptionForIndex(opt, logical_index)
        opt.rect = rect
        opt.text = ""
        self.style().drawControl(QStyle.ControlElement.CE_Header, opt, painter, self)
        model = self.model()
        if model is None:
            return
        raw = model.headerData(
            logical_index,
            Qt.Orientation.Horizontal,
            Qt.ItemDataRole.DisplayRole,
        )
        text = str(raw) if raw is not None else ""
        painter.save()
        painter.drawText(
            rect.adjusted(6, 4, -6, -4),
            int(Qt.AlignmentFlag.AlignCenter | Qt.TextWordWrap),
            text,
        )
        painter.restore()

    def sectionSizeFromContents(self, logical_index: int) -> QSize:
        model = self.model()
        text = ""
        if model is not None:
            raw = model.headerData(
                logical_index,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            if raw is not None:
                text = str(raw)
        w = max(self.sectionSize(logical_index), 40)
        br = self.fontMetrics().boundingRect(
            0,
            0,
            max(w - 12, 1),
            10_000,
            int(Qt.AlignmentFlag.AlignCenter | Qt.TextWordWrap),
            text,
        )
        h = max(br.height() + 12, 32)
        return QSize(w, h)
