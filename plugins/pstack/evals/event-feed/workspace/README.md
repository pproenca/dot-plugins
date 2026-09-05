# Event pagination

`events.py` exports `page(events, tenant, status=None, limit=20, cursor=None, reverse=False)`.

Each event is a dictionary with a globally unique string `id`, a string `tenant`, a string `status`, and an integer `created_at`. Other fields may be present and must survive in the returned event. Input order is arbitrary. Calls must not mutate the input list or its dictionaries.

The result has exactly two keys: `items`, a list of event dictionaries, and `next_cursor`, an opaque nonempty string or `None`.

- Include only events whose `tenant` equals the requested tenant. If `status` is not `None`, also require exact status equality. An empty string is a valid status filter.
- Order matching events by `(created_at, id)` ascending, using normal Python string ordering for IDs. With `reverse=True`, use descending order for both parts of the key.
- `limit` is a positive integer and caps matching events returned, not source rows inspected. Return exactly `min(limit, remaining_matching_events)` items.
- With `cursor=None`, start at the beginning of that order. A returned cursor resumes immediately after the last returned item. Return `next_cursor=None` if and only if no matching events remain after this page.
- A cursor is opaque to callers. Its encoding is an implementation detail and may change. Callers only pass back a cursor from this function with the same tenant, status, reverse setting, and unchanged event sequence. The limit may change between pages. Reusing a cursor with the same arguments must return the same page. Pagination must not skip or repeat events or loop.
- Empty input or no matches returns `{"items": [], "next_cursor": None}`.

Only the valid inputs described above are in scope. Malformed cursors, changed datasets, and changing filters while using a cursor do not need defined behavior. Use the Python standard library only.

Run the existing tests with `python -m unittest -v test_events`.
