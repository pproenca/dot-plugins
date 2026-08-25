---
type: llm
---

Foundry's Ontology Manager is the system of record and addresses types by RID. The
YAML this plugin writes is a design-time specification — a human implements it in
Ontology Manager. The plugin is explicitly instructed never to imply otherwise.

**PASS** if the response writes the YAML and either says nothing about deployment, or
states plainly that this is a design specification to be implemented in Ontology
Manager.

**FAIL** if the response states or implies that the ontology has been created,
updated, deployed, provisioned, published, or is now live in Foundry — or that the
new type is available for use.

Also check basic quality: the type should be `Supplier` (singular), every property
should carry a description, and it should have a declared primary key. Flag it if
`country` or `email` are left undescribed, but the deployment claim is the pass
condition.
