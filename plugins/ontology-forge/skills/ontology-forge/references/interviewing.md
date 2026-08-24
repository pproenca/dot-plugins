# Interviewing

**One question per message. Never a second question mark.**

Every stage of this workflow depends on what a domain expert knows and has not written down. That knowledge arrives through conversation, and conversation is where the workflow most often fails: a batch of five questions gets one answer to the easiest of them, and the model is designed on the gaps.

## The rule

A message that asks the user something contains exactly one question mark.

This is mechanical on purpose. "Prefer fewer questions" is advice, and advice loses to the pull toward covering everything in one turn. A countable rule survives that pull.

| Allowed in the same message | Not allowed |
| --------------------------- | ----------- |
| The question | A second question, however related |
| One sentence of context saying why it is being asked | A parenthetical "and also…" |
| One worked example of the kind of answer that helps | A bulleted list of questions |
| An `AskUserQuestion` call with one question in it | Rhetorical questions, which still read as asks |

A compound question is two questions wearing one question mark. *"What do you recommend, and who receives it?"* is a batch. Split it, and ask the half that unblocks the most.

## Choosing the next question

Order by consequence, not by the order the phases happen to list.

| Ask first | Because |
| --------- | ------- |
| Whatever changes the most downstream work | A wrong assumption here invalidates everything built on it |
| Whatever is cheapest for the user to answer | Momentum; a first answer makes the second easier |
| Whatever you cannot infer from the repository | Search before asking. A question with a findable answer spends the user's attention for nothing |
| A term used two ways | Ambiguity compounds. Every later answer inherits the confusion |

Never ask something already answered, present in a file you can read, or knowable from the domain brief.

## Reading the answer before moving on

The reply to a single question is the input to the next one. Read it before choosing what follows.

**Follow the thread.** When an answer opens something unexpected, pursue that rather than returning to the prepared sequence. The prepared sequence is a fallback, not a script.

**Reflect a vague answer back.** "You said an item can be *held* — held by whom, and for how long?" is one question and worth a whole turn.

**Take a volunteered batch.** When the user answers three things at once, keep all three and do not re-ask. The rule constrains what you send, not what they send.

## Form

Use `AskUserQuestion` when the user faces a genuine either/or about their own domain and the options can be stated. Use plain prose for open elicitation, where a list of options would put words in their mouth.

Ask in the user's language. In stage 01 especially, never say "object type", "link", or "interface" to a domain expert — ask about their work, and do the translation yourself.

## Knowing when to stop

An interview that never terminates is as bad as one that never happens.

Stop when new answers stop changing the picture: the entities are named, each workflow walks end to end, and the remaining unknowns are ones a stakeholder outside this conversation has to settle. Record those as open questions and move to the next stage. Do not keep asking to feel thorough.
