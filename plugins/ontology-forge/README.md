# ontology-forge

Design and extend a [Palantir Foundry](https://www.palantir.com/docs/foundry/ontology/overview) ontology the domain-driven way.

Ontology design runs in three stages, and the order is the whole point:

**01 Understand the domain** → **02 Design the ontology** → **03 Map source data and logic**

A model designed from source schemas describes a database. A model designed from the domain describes the organization, and survives the next system migration. This plugin keeps the work in that order and applies Palantir's published best practices, structural guidance, and anti-pattern catalog at every step.

## Skills

| Skill | What it does |
| ----- | ------------ |
| `/ontology-forge:understand-domain` | Stage 01. Interviews you as the domain expert, separates entities from events from attributes from relationships, and writes a domain brief and glossary. No object types yet — deliberately. |
| `/ontology-forge:design-ontology` | Stage 02. Turns the brief into object types, links, interfaces, and action types, screens the result against all eight anti-patterns, and writes the YAML plus `DECISIONS.md`. |
| `/ontology-forge:map-sources` | Stage 03. Maps real datasets onto the model, records what was deliberately excluded, reconciles conflicting sources, and places each piece of logic in the right layer. |
| `/ontology-forge:extend-ontology` | Fits a new requirement into an existing model, preferring new linked types and interfaces over modifying established core types. Reports blast radius before changing anything. |
| `/ontology-forge:audit-ontology` | Fans out parallel reviewers across the anti-pattern catalog, verifies every finding against the files, and writes a ranked report. |

A sixth skill, `ontology-forge`, loads automatically whenever work touches an object model. It carries the principles and routes to the stage skills.

## What it produces

```text
ontology/
├── DOMAIN-BRIEF.md           # stage 01
├── GLOSSARY.md               # stage 01
├── DECISIONS.md              # why the model is shaped this way
├── object-types/<apiName>.yaml
├── link-types/<apiName>.yaml
├── interfaces/<apiName>.yaml
├── action-types/<apiName>.yaml
├── shared-properties/<apiName>.yaml
├── mappings/<objectType>.yaml   # stage 03
└── AUDIT.md                     # from /audit-ontology
```

**These files are a design specification, not deployable configuration.** Ontology Manager is the system of record, and Foundry addresses types by RID — there is no official on-disk format that round-trips into the platform. What the files give you is a model that gets code review, decisions that get version history, and an ontology an agent can read without platform access. You implement the result in Ontology Manager.

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
codex plugin marketplace add pproenca/dot-plugins
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
