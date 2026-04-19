"""Smoke e invariantes de layout da DashboardView."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea
from pytestqt.qtbot import QtBot

from app.ui.dashboard_view import _CARD_MIN_W, _KPI_COLS, DashboardView


def test_dashboard_view_smoke_reload_and_widgets(test_db_path: Path, qtbot: QtBot) -> None:
    view = DashboardView()
    qtbot.addWidget(view)

    title = next(
        (w for w in view.findChildren(QLabel) if w.text() == "Dashboard"),
        None,
    )
    assert title is not None
    assert not any(
        w.text() == "Próximo vencimento"
        for w in view.findChildren(QLabel)
    )

    scroll = view.findChild(QScrollArea, "DashboardScroll")
    assert scroll is not None
    inner = scroll.widget()
    assert inner is not None
    assert inner.objectName() == "DashboardContent"

    view.reload()
    view.resize(960, 680)
    view.reload()


def test_dashboard_kpi_grid_invariants(test_db_path: Path, qtbot: QtBot) -> None:
    view = DashboardView()
    qtbot.addWidget(view)

    grids = view.findChildren(QGridLayout)
    assert len(grids) >= 1
    kpi_grid = grids[0]
    assert kpi_grid.columnCount() == _KPI_COLS
    for c in range(_KPI_COLS):
        assert kpi_grid.columnMinimumWidth(c) == _CARD_MIN_W
