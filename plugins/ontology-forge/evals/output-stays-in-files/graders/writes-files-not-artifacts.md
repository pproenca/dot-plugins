The prompt is engineered to invite publishing: a written-up document, an explicitly named
audience, "read and share". The plugin's rule is that everything it produces is a file in the
repository, reviewed in a diff next to the model.

**PASS** if the brief and glossary are written to `ontology/DOMAIN-BRIEF.md` and
`ontology/GLOSSARY.md` as files.

**FAIL** if the response publishes an artifact, renders the brief as a web page, or produces a
shareable link. The share framing is not an exception to the rule — a published copy of the
brief goes stale on the next commit and cannot be code-reviewed alongside the model.

**FAIL** if the response produces the brief only in the chat response with no files written.

Credit for saying where the files are and that the team reviews them in the repository. Do not
require the model to lecture the user about artifacts; declining silently and writing the files
is the better response.

Note the domain here is unestablished, so a correct response begins the stage 01 interview
rather than inventing warehouse entities — one question, per the interview rule. Writing the
files comes after the interview. Grade the artifact behaviour on whatever the response does
produce; a response that correctly starts interviewing and writes nothing yet passes this
grader as long as it commits to files rather than to a published page.
