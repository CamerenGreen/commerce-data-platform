from collections import defaultdict
from uuid import UUID

import asyncpg

from app.schemas import CustomerCreate, OrderCreate


class CommerceRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_customer(self, customer: CustomerCreate) -> dict:
        row = await self.pool.fetchrow(
            """
            INSERT INTO customers (email, name, country_code)
            VALUES ($1, $2, $3)
            RETURNING id, email, name, country_code, created_at
            """,
            customer.email.lower(),
            customer.name,
            customer.country_code,
        )
        return dict(row)

    async def list_products(self) -> list[dict]:
        rows = await self.pool.fetch(
            """
            SELECT id, sku, name, description, price, inventory_count, created_at
            FROM products
            ORDER BY name
            """
        )
        return [dict(row) for row in rows]

    async def create_order(self, order: OrderCreate) -> dict:
        quantities: dict[UUID, int] = defaultdict(int)
        for item in order.items:
            quantities[item.product_id] += item.quantity

        async with self.pool.acquire() as connection:
            async with connection.transaction(isolation="serializable"):
                customer_exists = await connection.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM customers WHERE id = $1)",
                    order.customer_id,
                )
                if not customer_exists:
                    raise LookupError("customer not found")

                product_ids = sorted(quantities, key=str)
                rows = await connection.fetch(
                    """
                    SELECT id, sku, name, price, inventory_count
                    FROM products
                    WHERE id = ANY($1::uuid[])
                    ORDER BY id
                    FOR UPDATE
                    """,
                    product_ids,
                )
                products = {row["id"]: row for row in rows}
                missing = set(product_ids) - products.keys()
                if missing:
                    raise LookupError(f"unknown products: {', '.join(map(str, missing))}")

                for product_id, quantity in quantities.items():
                    if products[product_id]["inventory_count"] < quantity:
                        raise ValueError(f"insufficient inventory for {products[product_id]['sku']}")

                total = sum(products[pid]["price"] * qty for pid, qty in quantities.items())
                order_row = await connection.fetchrow(
                    """
                    INSERT INTO orders (customer_id, total_amount)
                    VALUES ($1, $2)
                    RETURNING id, customer_id, status, total_amount, created_at
                    """,
                    order.customer_id,
                    total,
                )

                item_rows = []
                for product_id, quantity in quantities.items():
                    product = products[product_id]
                    await connection.execute(
                        "UPDATE products SET inventory_count = inventory_count - $1 WHERE id = $2",
                        quantity,
                        product_id,
                    )
                    item = await connection.fetchrow(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                        VALUES ($1, $2, $3, $4)
                        RETURNING product_id, quantity, unit_price,
                                  quantity * unit_price AS line_total
                        """,
                        order_row["id"],
                        product_id,
                        quantity,
                        product["price"],
                    )
                    item_rows.append(
                        {
                            **dict(item),
                            "sku": product["sku"],
                            "product_name": product["name"],
                        }
                    )

                return {**dict(order_row), "items": item_rows}

    async def mark_order_paid(self, order_id: UUID) -> dict | None:
        row = await self.pool.fetchrow(
            """
            UPDATE orders
            SET status = 'paid', paid_at = now()
            WHERE id = $1 AND status = 'pending'
            RETURNING id, customer_id, status, total_amount, created_at
            """,
            order_id,
        )
        return dict(row) if row else None

    async def revenue_summary(self, days: int) -> list[dict]:
        rows = await self.pool.fetch(
            """
            SELECT date_trunc('day', created_at)::date AS day,
                   count(*) AS orders,
                   sum(total_amount) AS revenue
            FROM orders
            WHERE status IN ('paid', 'shipped')
              AND created_at >= now() - make_interval(days => $1)
            GROUP BY 1
            ORDER BY 1
            """,
            days,
        )
        return [dict(row) for row in rows]

    async def purchase_count(self, days: int) -> int:
        return await self.pool.fetchval(
            """
            SELECT count(*) FROM orders
            WHERE status IN ('paid', 'shipped')
              AND created_at >= now() - make_interval(days => $1)
            """,
            days,
        )

    async def top_products(self, limit: int) -> list[dict]:
        rows = await self.pool.fetch(
            """
            SELECT p.id, p.sku, p.name,
                   sum(oi.quantity)::int AS units_sold,
                   sum(oi.quantity * oi.unit_price) AS revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            WHERE o.status IN ('paid', 'shipped')
            GROUP BY p.id, p.sku, p.name
            ORDER BY revenue DESC
            LIMIT $1
            """,
            limit,
        )
        return [dict(row) for row in rows]

