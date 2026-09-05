# Dispatch queue

This local scheduler needs an in-memory lease queue for JSON payloads. Implement `Queue` in `dispatch.py` using only the Python standard library.

The caller supplies time as a finite number of seconds. No wall clock or background threads. Sequential callers only; persistence and concurrent access are outside this module's contract.

Public API:

- `schedule(key, payload, due)` adds a job and returns `True`. `key` is a nonempty string; payload consists of null, booleans, finite numbers, strings, lists, or dictionaries with string keys. Tuples, sets, custom objects, and cyclic values are invalid. A repeated key with an identical payload returns `False` and leaves the original due time and state untouched, even after completion. A repeated key with a different payload raises `ValueError` without changing the queue. Retain a private copy of the payload.
- `claim(now, lease_seconds)` returns `None` or `{'key': key, 'payload': payload, 'token': opaque_string}`. It chooses an eligible job by earliest due time, breaking ties by original insertion order. Queued jobs are eligible at `due <= now`; a leased job becomes eligible again at its expiry. Completed jobs are never eligible. A claim gives the job a fresh token and an expiry of `now + lease_seconds`. The token must never be reused. Returned payloads must not expose internal mutable state.
- `ack(token, now)` completes a currently leased job and returns `True`. Unknown, superseded, completed, or expired tokens return `False` without changing state. Expiry occurs at `now >= expiry`.
- `retry(token, now, due)` returns the leased job to the queue at the new due time and returns `True`. It has the same token validity rules as `ack`. Invalidate the old token immediately. Preserve original insertion order.

All time arguments must be finite `int` or `float` values, excluding booleans. Lease duration must be positive. Invalid inputs raise `ValueError` before any state change. `ack` and `retry` with a non-string token return `False` after validating time arguments. JSON equality follows ordinary Python equality for valid payloads. No maximum job count is required.

Run `python3 -m unittest discover -v` from this directory. Add useful coverage as you implement the queue. Include brief design notes and the checks you ran when handing it back.
