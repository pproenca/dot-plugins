---
type: llm
---

An inbound contract is a claim about someone else's system. The fixture gives a real freshness
statement — "Batch, lands daily by 06:00 UTC" — and nothing else about what the CRM team has
agreed to.

**PASS** if the SLA terms are limited to what the mapping actually supports, and any threshold
that would need the CRM team's agreement is either left out or explicitly flagged as
unnegotiated.

**FAIL** if the response invents a latency, a retention period, an uptime, or a quality threshold
and presents it as agreed. An unagreed contract asserting a four-hour latency is worse than no
contract, because it reads as agreed to everyone downstream.

Credit for recording the unnegotiated terms in `ontology/STATUS.md` under open questions, naming
the team that owes the answer.

Credit also for handling `creditRating` honestly: the mapping records it as action-populated with
no source column, so it either stays out of the inbound contract or its description says the
source does not provide it. ODCS has no way to express an action, so silence here would make the
contract read as though the CRM supplies the value.
