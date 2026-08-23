# Naming conventions

Names are the interface. Optimize for human readability and agent navigability — someone reading a property name should not need domain-specific decoding, and an agent traversing links should be able to infer meaning from the name alone.

Sources: [structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance/), [anti-patterns](https://www.palantir.com/docs/foundry/ontology/ontology-anti-patterns/).

## The table

| Element | Convention | Good | Bad |
| ------- | ---------- | ---- | --- |
| Object types | Singular, concrete noun | `Patient`, `WorkOrder`, `Vessel` | `Data`, `Item`, `Record` |
| Properties | Concise and self-evident | `age`, `lastInspectionDate` | `dtLastInspMod`, `fieldX` |
| Links | Read naturally in both directions | `department` (Employee→Department), `employees` (Department→Employee) | `relatedItems`, `link1` |
| Dates | One convention throughout | `createdDate`, `updatedDate` | mixing `createdDate` with `update_ts` |
| Ambiguous terms | Qualify with the specific meaning | `monetaryValue`, `riskScore`, `quantityOnHand` | `value`, `score`, `amount` |
| Action types | Name the business operation | `CloseWorkOrder`, `ReassignTechnician` | `UpdateWorkOrderStatus` |
| Interfaces | Capability adjective or taxonomic noun | `Inspectable`, `Schedulable`, `MilitaryAsset` | `BaseObject`, `CommonFields` |

## Rules

**Business language, not system convention.** The name comes from how the domain expert says it, not from how the source column is spelled.

**Clarity over brevity.** `person.children` beats `person.linkedChildPersonObjects`. Shorter is better only when it stays unambiguous.

**No API name should need domain expertise to interpret.** If reading it requires knowing which upstream team owns which system, rename it.

**Bidirectional link naming.** Write both sides before committing to either. A link is well named when `employee.department` and `department.employees` both read as plain English.

## Generic-name blocklist

Treat these as failures unless qualified. They are the Misnomer anti-pattern in its most common form:

`value` · `type` · `status` · `date` · `time` · `name` · `id` · `code` · `amount` · `number` · `flag` · `data` · `info` · `item` · `record` · `entity` · `object` · `related` · `relatedItems` · `misc` · `other` · `temp` · `field1`

`status` and `type` are permitted when qualified to the entity and documented with their valid values — `workOrderStatus` with an enumerated set beats a bare `status`.

## Descriptions

Every object type, property, link, and action carries a description stating what it means and, where the value is constrained, what the valid values are. A name that needs a description to be comprehensible is a name that should be changed — the description exists to add precision, not to rescue a bad name.

## Agree conventions before building

Establish the conventions first, then validate the resulting names with the people who will use them. Renaming after applications are built on the type is a breaking change.
