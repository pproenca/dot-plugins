# Decisions

## workOrderCount is derived, and counts every state

**Date:** 2026-08-23
**Principle:** Normalization — store each fact once.

Counting linked work orders at query time cannot drift. Storing the count on
the asset would require every raise, close, and cancel path to update it.

**Tradeoff, and an unmet requirement:** derived aggregations take no predicate,
so this is a lifetime total including complete and cancelled work — not the
open-work-order backlog originally asked for. The property is named for what it
returns rather than what was wanted. Operations still need the backlog figure;
that requires a stored property with a pipeline maintaining it, and is not built.

Derived properties also cannot be text-searched, which the same fix would resolve.

## Technician assignment is an object-backed link

**Date:** 2026-08-23
**Principle:** Links carry no metadata; relationships that do need an object.

An assignment has a capacity and a start date. Putting those on the technician
breaks as soon as somebody works two jobs.
