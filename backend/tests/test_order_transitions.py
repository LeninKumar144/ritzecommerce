"""Order status transition rules."""

import pytest

from app.models.enums import OrderStatus
from app.services.orders import can_transition


@pytest.mark.parametrize(
    ("current", "target", "allowed"),
    [
        (OrderStatus.PENDING_PAYMENT, OrderStatus.CONFIRMED, True),
        (OrderStatus.PENDING_PAYMENT, OrderStatus.SHIPPED, False),
        (OrderStatus.CONFIRMED, OrderStatus.CANCELLED, True),
        (OrderStatus.DELIVERED, OrderStatus.REFUNDED, True),
        (OrderStatus.CANCELLED, OrderStatus.CONFIRMED, False),
        (OrderStatus.REFUNDED, OrderStatus.DELIVERED, False),
    ],
)
def test_order_transitions(current: OrderStatus, target: OrderStatus, allowed: bool) -> None:
    assert can_transition(current, target) is allowed
