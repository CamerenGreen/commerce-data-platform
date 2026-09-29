INSERT INTO products (id, sku, name, description, price, inventory_count) VALUES
('00000000-0000-4000-8000-000000000001', 'MECH-KEY-01', 'Nimbus Mechanical Keyboard', 'Hot-swappable 75% keyboard', 129.00, 75),
('00000000-0000-4000-8000-000000000002', 'MOUSE-ERG-01', 'Arc Ergonomic Mouse', 'Wireless vertical mouse', 69.00, 120),
('00000000-0000-4000-8000-000000000003', 'DESK-MAT-01', 'Orbit Desk Mat', 'Recycled-felt desk mat', 35.00, 200),
('00000000-0000-4000-8000-000000000004', 'HUB-USB-01', 'Beacon USB-C Hub', 'Eight-port USB-C hub', 89.00, 90),
('00000000-0000-4000-8000-000000000005', 'STAND-LAP-01', 'Summit Laptop Stand', 'Adjustable aluminum stand', 79.00, 60);

INSERT INTO customers (id, email, name, country_code, created_at) VALUES
('10000000-0000-4000-8000-000000000001', 'maya@example.com', 'Maya Chen', 'US', now() - interval '40 days'),
('10000000-0000-4000-8000-000000000002', 'jordan@example.com', 'Jordan Rivera', 'CA', now() - interval '20 days'),
('10000000-0000-4000-8000-000000000003', 'sam@example.com', 'Sam Okafor', 'GB', now() - interval '10 days');

WITH inserted_order AS (
    INSERT INTO orders (id, customer_id, status, total_amount, created_at, paid_at)
    VALUES (
        '20000000-0000-4000-8000-000000000001',
        '10000000-0000-4000-8000-000000000001',
        'paid', 198.00, now() - interval '5 days', now() - interval '5 days'
    )
    RETURNING id
)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT id, '00000000-0000-4000-8000-000000000001', 1, 129.00 FROM inserted_order
UNION ALL
SELECT id, '00000000-0000-4000-8000-000000000002', 1, 69.00 FROM inserted_order;

