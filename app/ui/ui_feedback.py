"""Ponto único para feedback global (toast) a partir de views sem acoplar à MainWindow."""
from __future__ import annotations

from collections.abc import Callable
from typing import Optional

_show_fn: Optional[Callable[[str, str | None, Callable[[], None] | None], None]] = None


def register_toast_handler(
    fn: Callable[[str, str | None, Callable[[], None] | None], None],
) -> None:
    global _show_fn
    _show_fn = fn


def show_toast(
    message: str,
    *,
    action_label: str | None = None,
    on_action: Callable[[], None] | None = None,
) -> None:
    if _show_fn is not None:
        _show_fn(message, action_label, on_action)
