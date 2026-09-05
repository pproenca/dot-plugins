---
name: principle-build-the-lever
description: "Automate repeated transformations or verification when a reusable tool improves consistency and reviewability."
---

# Build the lever

Use a deterministic tool when it makes repeated work cheaper or a result easier to verify. Reuse an existing command or script before building another.

For a repeated transformation, do one representative unit to learn the shape, automate it, and compare the automated result with that unit. Make reruns safe. A tool that handles every unit in one pass often beats agents applying the same edits by hand.

For independent workers following the same non-obvious procedure, a shared brief or skill can keep the contract consistent. Keep that contract outside their write scope.

Keep a new tool when future runs or review justify maintaining it. A one-off edit or check can use existing tools directly; applying this principle does not require adding a file to the diff.

See [Prove it works](../principle-prove-it-works/SKILL.md) for verification and [Encode lessons in structure](../principle-encode-lessons-in-structure/SKILL.md) for recurring constraints.
