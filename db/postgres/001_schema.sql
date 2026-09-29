CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE order_status AS ENUM ('pending', 'paid', 'shipped', 'cancelled');

CREATE TABLE customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL,
    name text NOT NULL CHECK (length(trim(name)) > 0),
    country_code char(2) NOT NULL CHECK (country_code = upper(country_code)),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT customers_email_unique UNIQUE (email),
    CONSTRAINT customers_email_lowercase CHECK (email = lower(email))
);

CREATE TABLE products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sku text NOT NULL UNIQUE,
    name text NOT NULL,
    description text,
    price numeric(12, 2) NOT NULL CHECK (price >= 0),
    inventory_count integer NOT NULL DEFAULT 0 CHECK (inventory_count >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid NOT NULL REFERENCES customers(id),
    status order_status NOT NULL DEFAULT 'pending',
    total_amount numeric(12, 2) NOT NULL CHECK (total_amount >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    paid_at timestamptz,
    CONSTRAINT paid_orders_have_timestamp CHECK (
        (status IN ('paid', 'shipped') AND paid_at IS NOT NULL)
        OR status IN ('pending', 'cancelled')
    )
);

CREATE TABLE order_items (
    order_id uuid NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id uuid NOT NULL REFERENCES products(id),
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12, 2) NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_orders_customer_created
    ON orders (customer_id, created_at DESC);

CREATE INDEX idx_orders_paid_created
    ON orders (created_at DESC)
    INCLUDE (total_amount)
    WHERE status IN ('paid', 'shipped');

CREATE INDEX idx_order_items_product
    ON order_items (product_id, order_id);

COMMENT ON COLUMN order_items.unit_price IS
    'Snapshot of product price at purchase time; historical totals do not change with catalog prices.';

