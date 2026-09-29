-- EXPLAIN-friendly examples for inspecting query plans.

-- 1) Covering partial index supports this revenue query without scanning pending orders.
EXPLAIN (ANALYZE, BUFFERS)
SELECT date_trunc('day', created_at)::date AS day,
       count(*) AS orders,
       sum(total_amount) AS revenue
FROM orders
WHERE status IN ('paid', 'shipped')
  AND created_at >= now() - interval '30 days'
GROUP BY 1
ORDER BY 1;

-- 2) Rank customers by lifetime value inside their country.
WITH customer_value AS (
    SELECT c.id, c.name, c.country_code,
           coalesce(sum(o.total_amount) FILTER (
               WHERE o.status IN ('paid', 'shipped')
           ), 0) AS lifetime_value
    FROM customers c
    LEFT JOIN orders o ON o.customer_id = c.id
    GROUP BY c.id
)
SELECT *, dense_rank() OVER (
    PARTITION BY country_code ORDER BY lifetime_value DESC
) AS country_rank
FROM customer_value
ORDER BY country_code, country_rank;

-- 3) Products commonly bought together (market-basket self join).
SELECT p1.name AS product_a, p2.name AS product_b, count(*) AS times_bought_together
FROM order_items a
JOIN order_items b ON a.order_id = b.order_id AND a.product_id < b.product_id
JOIN products p1 ON p1.id = a.product_id
JOIN products p2 ON p2.id = b.product_id
GROUP BY p1.name, p2.name
ORDER BY times_bought_together DESC;
