# Architecture decision record

## Context

Commerce Data Platform handles two workloads that look similar at the API but behave differently in storage:

1. Commerce operations update related rows and must never oversell inventory or lose monetary history.
2. Behavioral events arrive frequently, have evolving properties, and are mostly read as time-window aggregations.

## Decision: polyglot persistence

PostgreSQL owns commerce state. Its constraints are the final line of defense: references cannot dangle, quantity and money cannot be negative, emails and SKUs stay unique, and paid orders require a payment timestamp.

MongoDB owns behavioral events. Common fields are validated, while `properties` remains intentionally open for experiment metadata, search terms, referrers, device attributes, or product IDs. A globally unique `event_id` makes client retries safe.

Redis owns no durable state. It stores a JSON copy of computed funnel metrics under a time-window-specific key. Losing Redis only increases query cost; it does not lose business data.

## Critical flows

### Creating an order

1. Begin a PostgreSQL transaction at serializable isolation.
2. Verify the customer exists.
3. Combine duplicate product lines and sort product UUIDs.
4. Lock matching product rows in deterministic order with `FOR UPDATE`.
5. Reject missing products or insufficient inventory.
6. Insert the order, snapshot prices into line items, and decrement stock.
7. Commit all changes together.

Sorting lock acquisition reduces deadlock risk. Serializable isolation catches anomalies that row-level reasoning misses; clients receive a retryable conflict.

### Ingesting an event

The API validates the stable envelope, adds an ingestion timestamp, and inserts one MongoDB document. The unique `event_id` index turns duplicate delivery into an acknowledged no-op. This is at-least-once delivery compatible.

### Reading the dashboard

The service first checks Redis. On a miss, MongoDB groups events by type, PostgreSQL counts paid purchases and aggregates revenue, and the API combines the results. The funnel is cached briefly. A payment invalidates analytics keys; TTL handles missed invalidations.

## Consistency model

The system does not promise an atomic snapshot across PostgreSQL and MongoDB. Funnel metrics are operational analytics and tolerate seconds of lag. Orders, payments, totals, and inventory do not tolerate that lag, so they live in one ACID database.

This boundary avoids distributed transactions. If the product later requires every purchase to appear in an event stream, add a transactional outbox in PostgreSQL and an asynchronous publisher. The outbox row and order update would commit together.

## Index strategy

### PostgreSQL

- `orders(customer_id, created_at DESC)` supports customer history.
- A partial `orders(created_at DESC) INCLUDE (total_amount)` index only contains paid/shipped orders, matching revenue queries while staying smaller than a full index.
- `order_items(product_id, order_id)` supports product sales aggregation.
- Primary and unique constraints supply indexes for entity lookups, email, and SKU.

### MongoDB

- Unique `event_id` provides idempotency.
- `occurred_at` supports time-window scans.
- `(customer_id, occurred_at)` and `(session_id, occurred_at)` support ordered journeys.

Indexes accelerate reads but amplify writes and consume memory. These are tied to known queries; avoid speculative indexing.

## Failure modes

- **PostgreSQL unavailable:** commerce writes and combined analytics fail; no unsafe fallback is attempted.
- **MongoDB unavailable:** event ingestion and combined funnel reads fail, while PostgreSQL data remains intact.
- **Redis unavailable:** current implementation fails the analytics call. A production resilience improvement would catch cache errors and calculate directly.
- **API crashes during an order:** PostgreSQL rolls back the open transaction.
- **Event client retries:** unique `event_id` prevents duplication.
- **Concurrent purchases:** locked inventory rows serialize decrements; the check constraint adds defense in depth.

## Scaling path

Measure before splitting services. Likely steps are read replicas for catalog/history queries, time-based event retention, an outbox and stream processor for precomputed funnels, and horizontal API replicas. Only shard MongoDB after choosing a key from observed distribution and query locality.
