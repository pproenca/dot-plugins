# Inventory reservations

This module manages checkout holds for one in-memory inventory. Import `Inventory` from `inventory.py`. Use Python's standard library only. There are no background jobs, threads, persistence, or external services.

## Values and errors

SKU names and reservation keys are nonempty strings. They are case-sensitive and are used exactly as supplied. Quantities and timestamps are Python integers, excluding booleans. All timestamps are nonnegative.

Stock and item arguments are dictionaries mapping SKU names to quantities. Initial stock accepts zero quantities and an empty dictionary. Reservation and restock items must be nonempty, with strictly positive quantities.

Malformed argument types or values raise `ValueError`. An otherwise valid request for an unknown SKU or reservation key raises `KeyError`. Insufficient stock, a conflicting reservation replay, an invalid state transition, and a deadline that is not in the future raise `ValueError`.

Validate all arguments before changing state. Any call that raises must leave stock, reservations, and the clock unchanged. If an input has multiple errors, the order in which those errors are reported is unspecified.

The object owns its state. Later changes to input dictionaries or returned dictionaries, including nested item dictionaries, must not change inventory state. Results from separate calls must not share mutable state with each other. No particular internal representation is required.

## API

### `Inventory(initial_stock)`

Create an inventory with the supplied stock and no reservations. Its clock starts at zero. Separate instances have independent stock, reservations, and clocks.

### `stock()`

Return a dictionary containing currently available quantities for every known SKU, including those with zero availability. Held and captured units are unavailable. Released and expired units are available again.

### `restock(items)`

Add the quantities to available stock. This operation may introduce new SKUs. Return `None`.

### `reserve(key, items, expires_at)`

For a new key, hold all requested items if every SKU exists and has enough available units. The entire reservation succeeds or fails together. `expires_at` must be strictly greater than the current clock. Return a reservation record with exactly these fields:

```python
{
    "key": "checkout-17",
    "items": {"tea": 2, "mug": 1},
    "expires_at": 30,
    "status": "held",
}
```

A reservation key is retained for the life of the inventory. If that key already exists, identical items and `expires_at` return its current record without changing stock or extending the hold. Dictionary order does not matter. This replay works in every status, even after the deadline has passed. A different item quantity, SKU set, or deadline for an existing key raises `ValueError`. Arguments still have to satisfy the value and type rules on a replay.

### `get(key)`

Return the reservation record in its current status. Unknown keys raise `KeyError`.

### `capture(key)`

Change a `held` reservation to `captured`. The held units become sold and remain unavailable. Return its record. Capturing an already `captured` reservation returns its record without changing stock. Capturing a `released` or `expired` reservation raises `ValueError`.

### `release(key)`

Change a `held` reservation to `released` and restore its units to available stock. Return its record. Releasing an already `released` reservation returns its record without restoring stock again. Releasing a `captured` or `expired` reservation raises `ValueError`.

### `advance(now)`

Set the clock to `now`, which must be at least the current clock. Expire every `held` reservation whose `expires_at <= now`, restore those units, and set its status to `expired`. Other statuses remain unchanged. Advancing to the current time is allowed. Return `None`.

Only `advance` moves the clock or expires holds. All terminal statuses, `captured`, `released`, and `expired`, remain terminal. An expired key cannot be reused for a fresh hold.
