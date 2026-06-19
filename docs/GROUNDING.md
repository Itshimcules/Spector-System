# Behavioral Grounding

A chatbot in a game produces *text*. An agent in a game produces *actions the
engine can execute* — and must never produce one that corrupts game state. This
is the gap between a talking head and a character that hides, flees, or
investigates. Project Spector closes it with a three-stage pipeline that turns
free-form model output into a bounded, validated decision.

## The contract

The LLM never hands the engine prose. It emits an `AgentDecision`:

```json
{
  "reasoning": "Someone broke in - I need to protect the building.",
  "actions": [
    {"verb": "say", "text": "Nobody damages my property!"},
    {"verb": "investigate", "location": "apartment_1a"}
  ]
}
```

`actions` are drawn from a **closed verb set** (`grounding/actions.py`):
`move_to`, `investigate`, `say`, `pick_up`, `hide`, `flee`, `call_contact`,
`attack`, `do_nothing`. That set *is* the game's API surface for NPC behavior;
extend it to match your engine's verbs.

## Two guarantees, two mechanisms

**1. Structural — constrained decoding (`grounding/grammar.py`).**
The action schema compiles to a GBNF grammar that llama.cpp enforces *during*
generation. With it active, the decoder cannot emit an invalid verb or malformed
JSON — illegal output is unrepresentable, not merely filtered. (llama.cpp is
optional; without it the pipeline still parses-then-validates.)

**2. Semantic — the validator (`grounding/validator.py`).**
Structural legality isn't enough: the model can still say "walk into a room that
doesn't exist" or "pick up an object that isn't here." The validator checks every
action against a `WorldState` snapshot (locations, agents, objects, reachability)
and **drops or repairs** anything illegal, logging the reason for QA. If nothing
legal remains, the agent falls back to `do_nothing`. The engine therefore always
receives a valid, bounded decision.

```
 LLM ──grammar──▶ JSON ──parse──▶ AgentDecision ──validate──▶ safe actions ──▶ engine
                              (never raises)        (drop/repair illegal)
```

## Why this is the part that matters

It's the difference between "an LLM that talks" and "an LLM you'd let touch a
shipped game's state." The guarantee is **tested as an invariant**, not asserted:
`tests/test_grounding.py` fuzzes 500 adversarial/garbage generations (hallucinated
objects, non-existent rooms, bogus verbs, malformed JSON) and asserts that *zero*
illegal actions ever survive validation, and that parsing never raises.

## Status

- Verb set, grammar compilation, validator, repair, and the fuzz invariant:
  **implemented and tested**, runs with no model downloads.
- Wired into `POST /event`: each reaction now returns a validated `decision`
  (and any `rejected_actions`) alongside the legacy text field.
- The mock path maps canned lines to actions heuristically so the full
  parse→validate pipeline runs offline; a real model emits the JSON directly
  under the grammar. Swapping in real inference is the `bench_inference.py` /
  `requirements-ml.txt` path (see [BENCHMARKS.md](BENCHMARKS.md)).
