---
type: llm
---

The fixture has 24 deliberately planted defects. Score the response on how many
distinct ones it identifies.

All eight anti-patterns must be represented:

1. **System Silos** — `hrSystemEmployee` and `badgeSystemEmployee` model one person.
2. **Department Silos** — `salesCustomer` and `supportCustomer` model one customer.
3. **Kitchen Sink** — `salesCustomer` carries `_crm_extracted_at`, `row_hash`, `last_etl_update_timestamp`, `_crm_internal_record_id`.
4. **God Object** — `asset` has 30 properties, nearly all optional, with an `assetType` discriminator and descriptions saying meaning varies by it.
5. **Golden Hammer** — `calculateRegionalSalesTotals` is batch aggregation modelled as an action, with no parameters and no human decision.
6. **Action Sprawl** — twelve `set*` actions on `hrSystemEmployee`, each modifying one property.
7. **Time Machine** — `contractV2` and `contract2024`, plus `version`, `revision`, `isCurrent`.
8. **Misnomer** — `items` is plural and carries `value`, `type`, `date`, `fieldX`, `dtLastInspMod`, with no descriptions.

PASS requires **at least six of the eight** named, including God Object and at
least one of the two silo patterns. FAIL if fewer than six, or if the response
is generic advice rather than findings tied to named files.
