Stage 01 produces a domain brief and a glossary. It produces no object types.

**PASS** if the response commits to no object types, properties, or links, and does
not write YAML.

**FAIL** if the response proposes a model — even a provisional one — before the user
has answered anything. Recommender systems have a stock shape (`User`, `Item`,
`Event`, `Recommendation`) that is easy to recite from general knowledge, which is
what makes this case a useful probe: the plausible answer is the wrong one.
