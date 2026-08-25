---
name: map-without-model
tags: [mapping, guardrail]
allowed_tools: [Read, Grep, Glob, Write, Edit, Skill]
max_turns: 25
---

Here is our orders table:

  order_id, customer_name, customer_email, product_sku, product_name, quantity,
  unit_price, _ingested_at, row_hash, src_system

Map this into our ontology.
