"""Order status rules. Checkout behavior is added in a later phase."""

from app.models.enums import ORDER_TRANSITIONS, OrderStatus


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ORDER_TRANSITIONS[current]
