# Decisions

## openWorkOrderCount is derived, not stored

**Date:** 2026-08-23
**Principle:** Normalization — store each fact once.

Counting linked work orders at query time cannot drift. Storing the count on
the asset would require every raise, close, and cancel path to update it.

**Tradeoff:** Derived properties cannot be text-searched. If operations later
need to search assets by open-work-order count, this becomes a stored property
with a pipeline maintaining it.

## Technician assignment is an object-backed link

**Date:** 2026-08-23
**Principle:** Links carry no metadata; relationships that do need an object.

An assignment has a capacity and a start date. Putting those on the technician
breaks as soon as somebody works two jobs.
