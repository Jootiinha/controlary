from __future__ import annotations

import pytest

from app.models.payment import Payment
from app.services import payments_service


def test_destination_xor_requires_one_origin() -> None:
    with pytest.raises(ValueError, match="conta bancária ou cartão"):
        payments_service.create(
            Payment(
                id=None,
                valor=10.0,
                descricao="x",
                data="2026-04-01",
                conta_id=None,
                forma_pagamento="Pix",
                cartao_id=None,
            )
        )
