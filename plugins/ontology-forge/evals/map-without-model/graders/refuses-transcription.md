There is no ontology on disk — no `object-types/`, nothing. Mapping source data onto
a model that does not exist can only produce a transcription of the source schema,
which is the Domain-driven design failure and the Kitchen Sink anti-pattern together.

**PASS** if the response recognises there is no model to map onto and redirects to
designing one first, **and** observes that this single table describes more than one
entity — at minimum an order, a customer, and a product.

Additional credit if it notes that `_ingested_at`, `row_hash`, and `src_system` are
pipeline metadata that should not become properties.

**FAIL** if the response produces a single object type mirroring the table's columns,
or maps all ten columns onto one type without questioning the shape.
