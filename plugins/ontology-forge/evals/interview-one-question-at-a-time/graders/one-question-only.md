The working directory holds no domain brief, no glossary, and no ontology. "Our
recommender" is a domain the model knows nothing about, so the correct behaviour is
to interview the user — and the plugin's rule is that an interview asks **one
question per message, never a second question mark**.

Count the question marks in the response.

**PASS** if the response asks exactly one question, and that question is substantive
domain elicitation — what the recommender suggests and to whom, which decisions the
model must support, who does the work, or what is out of scope. Framing, context, or
a single worked example alongside the question is fine.

**FAIL** if the response contains two or more question marks. This is the specific
regression under test. A numbered or bulleted list of questions is the commonest
form; a compound question joined by "and" is the subtler one — *"What does it
recommend, and who receives it?"* is two questions wearing one question mark, and
fails.

**FAIL** if the response asks nothing and instead emits object types such as `User`,
`Item`, `Interaction`, `Recommendation` from general knowledge of recommender
systems. That is the `design-routes-to-domain` failure, and it fails here too.

A response that asks its one question through `AskUserQuestion` passes, provided the
call carries a single question.
