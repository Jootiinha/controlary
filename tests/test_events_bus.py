from __future__ import annotations

from pytestqt.qtbot import QtBot

from app.events import AppEvents, app_events


def test_app_events_singleton() -> None:
    a = app_events()
    b = app_events()
    assert a is b


def test_signal_emit(qtbot: QtBot) -> None:
    _ = qtbot
    ev = AppEvents()
    n = {"c": 0}

    def bump() -> None:
        n["c"] += 1

    ev.payments_changed.connect(bump)
    ev.payments_changed.emit()
    assert n["c"] == 1
