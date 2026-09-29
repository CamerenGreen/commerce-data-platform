db = db.getSiblingDB("commerce_data");

db.createCollection("events", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["event_id", "session_id", "event_type", "occurred_at", "properties"],
      properties: {
        event_id: { bsonType: "string" },
        customer_id: { bsonType: ["string", "null"] },
        session_id: { bsonType: "string" },
        event_type: {
          enum: ["page_view", "product_view", "search", "add_to_cart", "checkout_started"]
        },
        occurred_at: { bsonType: "date" },
        ingested_at: { bsonType: "date" },
        properties: { bsonType: "object" }
      }
    }
  }
});

db.events.createIndex({ event_id: 1 }, { unique: true });
db.events.createIndex({ occurred_at: 1 });
db.events.createIndex({ customer_id: 1, occurred_at: 1 });
db.events.createIndex({ session_id: 1, occurred_at: 1 });

const now = new Date();
const productId = "00000000-0000-4000-8000-000000000001";
const customerId = "10000000-0000-4000-8000-000000000001";
const types = [
  "product_view", "product_view", "product_view", "product_view",
  "add_to_cart", "add_to_cart", "checkout_started"
];

db.events.insertMany(types.map((eventType, index) => ({
  event_id: `30000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`,
  customer_id: customerId,
  session_id: `demo-session-${Math.floor(index / 3) + 1}`,
  event_type: eventType,
  occurred_at: new Date(now.getTime() - index * 3600000),
  ingested_at: now,
  properties: { product_id: productId, source: "seed" }
})));
