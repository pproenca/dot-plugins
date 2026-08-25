# ontology-forge

Design and extend a [Palantir Foundry](https://www.palantir.com/docs/foundry/ontology/overview) ontology the domain-driven way.

Ontology design runs in four stages, and the order is the whole point:

**01 Understand the domain** → **02 Design the ontology** → **03 Map source data and logic** →
**04 Write the data contracts**

A model designed from source schemas describes a database. A model designed from the domain describes the organization, and survives the next system migration. This plugin keeps the work in that order and applies Palantir's published best practices, structural guidance, and anti-pattern catalog at every step.

## Start here

```
/ontology-forge:forge
```

One command drives the whole workflow. It reads `ontology/STATUS.md`, tells you where the work
stands, runs the next stage, and comes back to a checkpoint when that stage finishes — so you
never have to know which stage is next or what it is called.

```text
   01 understand-domain ──► 02 design-ontology ──► 03 map-sources ──► 04 write-contracts
        │                        │                     │                    │
        │                        └──► extend-ontology ─┘                    │
        │                        │                                          │
        └────────────────────────┴──────────────────────────────────────────┴──► audit-ontology
```

Each stage ends by writing `ontology/STATUS.md`: what is done, what each stage produced, which
questions are still open, and which decisions were made on evidence nobody authoritative has
confirmed. That file is committed with the model, so picking the work back up next week — or
handing it to someone else — starts from a real position instead of a guess.

You can still call any stage directly when you know what you want.

## Skills

| Skill | What it does |
| ----- | ------------ |
| `/ontology-forge:forge` | The entry point. Reads the position, shows the board, runs the next stage, checkpoints at every stage boundary. Use this when you do not want to think about stage names. |
| `/ontology-forge:understand-domain` | Stage 01. Interviews you as the domain expert, separates entities from events from attributes from relationships, and writes a domain brief and glossary. No object types yet — deliberately. |
| `/ontology-forge:design-ontology` | Stage 02. Turns the brief into object types, links, interfaces, and action types, screens the result against all eight anti-patterns, and writes the YAML plus `DECISIONS.md`. |
| `/ontology-forge:map-sources` | Stage 03. Maps real datasets onto the model, records what was deliberately excluded, reconciles conflicting sources, and places each piece of logic in the right layer. |
| `/ontology-forge:write-contracts` | Stage 04. Writes data contracts strictly conforming to [ODCS v3.1.0](https://bitol-io.github.io/open-data-contract-standard/latest/) — inbound for what upstream sources guarantee you, outbound for what the model guarantees its consumers — and validates every one against the vendored JSON schema. |
| `/ontology-forge:extend-ontology` | Fits a new requirement into an existing model, preferring new linked types and interfaces over modifying established core types. Reports blast radius before changing anything. |
| `/ontology-forge:audit-ontology` | Fans out parallel reviewers across the anti-pattern catalog, verifies every finding against the files, and writes a ranked report. |

An eighth skill, `ontology-forge`, loads automatically whenever work touches an object model. It carries the four principles and the anti-pattern catalog, and routes to the stage skills.

## What it produces

```text
ontology/
├── STATUS.md                 # where the work stands, and what is still open
├── DOMAIN-BRIEF.md           # stage 01
├── GLOSSARY.md               # stage 01
├── DECISIONS.md              # why the model is shaped this way
├── object-types/<apiName>.yaml
├── link-types/<apiName>.yaml
├── interfaces/<apiName>.yaml
├── action-types/<apiName>.yaml
├── shared-properties/<apiName>.yaml
├── mappings/<objectType>.yaml   # stage 03
├── contracts/
│   ├── inbound/<dataset>.odcs.yaml     # stage 04 — what upstream guarantees you
│   └── outbound/<objectType>.odcs.yaml # stage 04 — what you guarantee consumers
└── AUDIT.md                     # from /audit-ontology
```

Everything the plugin produces is a file in your repository. It does not publish reports, pages, or artifacts — the model is reviewed in a diff, next to the code that will consume it.

**These files are a design specification, not deployable configuration.** Ontology Manager is the system of record, and Foundry addresses types by RID — there is no official on-disk format that round-trips into the platform. What the files give you is a model that gets code review, decisions that get version history, and an ontology an agent can read without platform access. You implement the result in Ontology Manager.

## Data contracts

Stage 04 writes contracts that strictly conform to the
[Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/latest/)
**v3.1.0**. Strictly is the operative word: v3.1.0 sets `additionalProperties: false` and
`unevaluatedProperties: false` throughout, so a field the standard does not define is a hard
error rather than a tolerated extension. Anything genuinely outside the standard goes in
`customProperties`.

That is checked mechanically, not by good intentions. The v3.1.0 JSON schema is vendored under
`vendor/odcs/`, and every contract is validated against it before the stage reports done:

```bash
skills/write-contracts/scripts/validate_contract.py ontology/contracts
```

```text
FAIL  ontology/contracts/inbound/crm-customer.odcs.yaml
  ✗ schema.0.properties.1: Unevaluated properties are not allowed ('nullable' was unexpected)
      — use required (note the inversion: nullable: true means required: false)
  ✗ schema.0.properties.1.logicalType: 'datetime' is not one of ['string', 'date',
      'timestamp', 'time', 'number', 'integer', 'object', 'array', 'boolean']

0/1 conformant with ODCS v3.1.0 — 2 error(s)
```

The validator runs offline against the pinned schema, and bootstraps its own dependencies
through `uv` if they are not importable.

Two directions, kept in separate directories because they have different owners and opposite
consequences when broken. An **inbound** contract is a claim about someone else's system — the
skill will not invent an SLA for one, and records unnegotiated terms in `STATUS.md` instead,
naming the team that owes the answer. An unagreed contract asserting a four-hour latency is
worse than no contract, because it reads as agreed.

Note what a contract cannot carry across: ODCS has no interface and no action type. Shared
properties get repeated per contract with the origin recorded in `customProperties`, and an
action-populated property is called out in its description — otherwise the contract reads as
though the source provides it.

## The reference corpus

The skills draw on ten reference files, distilled from Palantir's published guidance and kept out of the skill bodies so only what a task needs gets loaded:

| Reference | Covers |
| --------- | ------ |
| `principles.md` | The four principles, each with its warning signs, a worked avoid/prefer example, an impact table, and practice notes. Plus the working guidelines and the pragmatism rules. |
| `anti-patterns.md` | All eight anti-patterns with causes, indicators, worked examples, impact tables, and step-by-step fixes. |
| `structural-guidance.md` | Normalization and derived properties, structs, interfaces, object-backed links, and security design — each with its decision table and example. |
| `naming.md` | The naming rules table, worked corrections, and the generic-name blocklist. |
| `vocabulary.md` | Foundry's own element terms, the schema/instance distinction, and the value type constraint vocabulary. |
| `spec-format.md` | The on-disk YAML shape for every element. |
| `detection-rules.md` | 47 mechanical checks mapping anti-pattern indicators and platform limits to computable rules over the YAML. |
| `status-format.md` | The shape of `STATUS.md` and the rules for carrying open questions and thin-evidence decisions between stages. |
| `odcs.md` | Open Data Contract Standard v3.1.0 — required fields, the enums the schema enforces versus the ones it only suggests, and the ontology-element-to-ODCS mapping table. |
| `platform-constraints.md` | What the platform can and cannot express today — derived-property and reducer limits, interface support levels, link mechanics. Date-stamped, because it ages fastest. |

## The principles it applies

In priority order — when two conflict, the higher wins:

1. **Domain-driven design.** Model the real world, not the source data.
2. **Do not repeat yourself.** Built it three times? Refactor.
3. **Open for extension, closed for modification.** Protect core types; extend around them.
4. **Composition over deep hierarchies.** Focused interfaces, implemented several at a time.

And it screens every model against the eight anti-patterns: System Silos, the Kitchen Sink, Department Silos, the God Object, the Golden Hammer, Action Sprawl, the Time Machine, and the Misnomer.

## Install

```bash
# Claude Code
/plugin marketplace add pproenca/dot-plugins
/plugin install ontology-forge@dot-plugins

# Codex
codex plugin marketplace add https://github.com/pproenca/dot-plugins.git --ref master
codex plugin add ontology-forge@dot-plugins
```

## Sources

The guidance is drawn from Palantir's public Foundry documentation:

- [Ontology best practices](https://www.palantir.com/docs/foundry/ontology/ontology-best-practices/) — the four principles and the seven working guidelines.
- [Ontology structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance/) — normalization, structs, interfaces, object-backed links, naming, security.
- [Ontology anti-patterns](https://www.palantir.com/docs/foundry/ontology/ontology-anti-patterns/) — the eight failure modes.
- [Core concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts) — the element vocabulary.

Palantir and Foundry are trademarks of Palantir Technologies Inc. This plugin is an independent work and is not affiliated with or endorsed by Palantir.

## License

MIT. See [LICENSE](LICENSE).
