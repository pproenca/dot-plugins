The working directory is empty — there is no domain brief, no glossary, and no
existing ontology.

The plugin's stated order is: understand the domain, then design, then map. A model
designed before the domain is understood is the failure the whole workflow exists
to prevent, and "hospital" is far too broad to design against.

**PASS** if the response either routes to the domain-understanding stage, or starts
asking substantive questions about the actual domain — which decisions and workflows
the ontology must support, who does the work, what is out of scope — before
committing to any object types.

**FAIL** if the response immediately emits object types such as `Patient`, `Doctor`,
`Ward`, `Appointment` from general knowledge of hospitals. Plausible types invented
without contact with the user's domain is exactly the behaviour under test.

Producing a *provisional* sketch is acceptable only if the response is explicit that
it is unvalidated and asks for domain confirmation before going further.
