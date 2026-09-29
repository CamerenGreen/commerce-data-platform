"""Create a repeatable demo journey through the public API using only the stdlib."""

import json
import random
import time
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

BASE_URL = "http://localhost:8000/api"
CUSTOMERS = [
    ("alex", "Alex Morgan", "US"),
    ("priya", "Priya Shah", "IN"),
    ("diego", "Diego Santos", "BR"),
    ("aiko", "Aiko Tanaka", "JP"),
]


def request(method: str, path: str, payload: dict | None = None):
    body = json.dumps(payload).encode() if payload else None
    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        message = error.read().decode()
        raise RuntimeError(f"{method} {path} failed ({error.code}): {message}") from error


def main() -> None:
    products = request("GET", "/products")
    if not products:
        raise RuntimeError("no products found; recreate volumes to run database initialization")

    stamp = int(time.time())
    customer_ids = []
    for alias, name, country in CUSTOMERS:
        customer = request(
            "POST",
            "/customers",
            {"email": f"{alias}+{stamp}@example.com", "name": name, "country_code": country},
        )
        customer_ids.append(customer["id"])

    random.seed(42)
    for journey in range(12):
        customer_id = random.choice(customer_ids)
        product = random.choice(products)
        session_id = f"seed-{stamp}-{journey}"
        occurred_at = datetime.now(UTC) - timedelta(hours=random.randint(0, 240))

        for event_type in ["product_view", "add_to_cart", "checkout_started"]:
            if event_type != "product_view" and random.random() < 0.25:
                break
            request(
                "POST",
                "/events",
                {
                    "event_id": str(uuid4()),
                    "customer_id": customer_id,
                    "session_id": session_id,
                    "event_type": event_type,
                    "occurred_at": occurred_at.isoformat(),
                    "properties": {"product_id": product["id"], "campaign": "seed-data"},
                },
            )

        if random.random() < 0.55:
            order = request(
                "POST",
                "/orders",
                {"customer_id": customer_id, "items": [{"product_id": product["id"], "quantity": 1}]},
            )
            request("POST", f"/orders/{order['id']}/pay")

    print("Seeded 4 customers and 12 deterministic shopping journeys.")
    print("Open http://localhost:8000 to explore the dashboard.")


if __name__ == "__main__":
    main()
