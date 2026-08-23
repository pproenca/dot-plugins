# Naming conventions

**Optimize for human readability and agent navigability.**

Consistent, descriptive naming is one of the most impactful investments in ontology quality. Clear names make the model easy for people *and* AI agents to navigate — and they are far harder to correct once the ontology is in use, because renaming after applications depend on a type is a breaking change.

Distilled from [structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance/) and [anti-patterns](https://www.palantir.com/docs/foundry/ontology/ontology-anti-patterns/).

## Naming rules

| Element | Convention | Good | Bad |
| ------- | ---------- | ---- | --- |
| Object types | Singular concrete nouns a domain expert would recognise | `Patient`, `WorkOrder`, `FlightSegment` | `Data`, `Item`, `Record` |
| Properties | Concise, self-evident; no encoded type info or implementation detail | `age`, `status`, `lastInspectionDate` | `dtLastInspMod`, `nVAL01`, `fieldX` |
| Links | Read naturally from each direction | `department` (Employee → Dept), `employees` (Dept → Employee) | `relatedItems`, `link1` |
| Dates | One convention, applied consistently across the whole ontology | `createdDate`, `updatedDate`, `effectiveDate` | Mixing `createdDate` and `dateOfCreation` |
| Ambiguous terms | Qualify with the specific meaning | `monetaryValue`, `quantityOnHand`, `riskScore` | `value`, `quantity`, `score` |
| Action types | Name the business operation | `TransferEmployee`, `ApprovePurchaseOrder`, `EscalateSupportTicket` | `UpdateEmployeeDepartment` |
| Interfaces | Capability adjective or taxonomic noun | `Inspectable`, `Schedulable`, `MilitaryAsset` | `BaseObject`, `CommonFields` |

## Worked corrections

| Instead of | Use |
| ---------- | --- |
| Object type `Item` | `Product` — or `SalesOrderLineItem`, or `WarehouseInventoryRecord`, depending which was meant |
| Property `dtLastInspMod` | `lastInspectionDate` |
| Property `value` | `monetaryValue` or `quantityOnHand` |
| Property `type` | `productCategory` or `serviceTier` |
| Property `date` | `orderPlacedDate` or `contractEffectiveDate` |
| Link `Item → Related Item` | `Product → Supplier`, `Employee → Supervisor` |

## Rules

**Business language, not system convention.** The name comes from how the domain expert says it, not how the source column is spelled.

**Clarity over brevity.** `person.children` beats `person.linkedChildPersonObjects`. Shorter wins only where it stays unambiguous.

**No API name should need domain expertise to decode.** If reading it requires knowing which team owns which upstream system, rename it.

**Follow the ontology's established conventions.** If the model already uses `createdDate`, do not introduce `dateOfCreation`. Consistency beats individually optimal names.

**Name links from both sides before committing.** A link is well named when `employee.department` and `department.employees` both read as plain English.

## Generic-name blocklist

Treat these as failures unless qualified — they are the Misnomer anti-pattern in its commonest form:

`value` · `type` · `status` · `date` · `time` · `name` · `id` · `code` · `amount` · `quantity` · `score` · `number` · `flag` · `data` · `info` · `item` · `record` · `entity` · `object` · `related` · `relatedItems` · `misc` · `other` · `temp` · `field1`

`status` and `type` are acceptable once qualified to the entity and documented with their valid values — `workOrderStatus` with an enumerated set beats a bare `status`.

## Descriptions

Every object type, property, link, and action carries a description stating what it means and, where values are constrained, what the valid values are.

A name that *needs* its description to be comprehensible is a name to change. Descriptions add precision; they do not rescue bad names. Where documentation becomes essential rather than supplementary, it will go stale and take the model's credibility with it.

## Governance

Agree the conventions before building — patterns for dates, statuses, identifiers, and links — and enforce them in review. Then validate the resulting names with the people who will use the ontology daily: names obvious to the builder are often ambiguous to consumers.
