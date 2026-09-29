from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import CustomerCreate, EventCreate, OrderCreate


def test_country_codes_are_normalized():
    customer = CustomerCreate(email="dev@example.com", name="Dev", country_code="us")
    assert customer.country_code == "US"


def test_order_requires_items():
    with pytest.raises(ValidationError):
        OrderCreate(customer_id=uuid4(), items=[])


def test_event_type_is_restricted():
    with pytest.raises(ValidationError):
        EventCreate(
            event_id=uuid4(),
            session_id="session-1",
            event_type="unknown",
            occurred_at=datetime.now(UTC),
        )

