"""
Grounding runtime - turn an LLM into a validated AgentDecision.

Two paths, one output contract:

  * Real model loaded  -> generate under the GBNF grammar, parse the JSON.
  * Mock mode          -> take the mock line and map it to a heuristic decision.

Either way the result goes through the validator, so callers always receive a
``ValidationResult`` whose actions are legal in the current world. The heuristic
mock path exists so the full grounding pipeline (parse + validate + repair) is
exercised end-to-end with no model downloads.
"""

import logging

from .actions import (
    AgentDecision,
    CallContact,
    DoNothing,
    Flee,
    Hide,
    Investigate,
    Say,
)
from .grammar import build_grammar
from .validator import ActionValidator, ValidationResult, WorldState

logger = logging.getLogger(__name__)


def parse_decision(raw) -> AgentDecision:
    """Parse model output into an AgentDecision, falling back to a safe default."""
    try:
        if isinstance(raw, dict):
            return AgentDecision.model_validate(raw)
        return AgentDecision.model_validate_json(raw)
    except Exception:
        return AgentDecision(
            reasoning="unparseable model output", actions=[DoNothing()]
        )


def heuristic_decision(text: str, focus_location=None) -> AgentDecision:
    """
    Map a mock free-text line to a structured decision using keyword cues.

    This stands in for a real model's tool-call so the grounding/validation path
    runs without any model files. It is intentionally simple - the validator,
    not this function, is what guarantees safety.
    """
    actions = [Say(text=text)]
    t = (text or "").lower()

    if any(k in t for k in ("hide", "scared", "can't deal", "cant deal", "oh no")):
        actions.append(Hide())
    if any(k in t for k in ("run", "flee", "get away")):
        actions.append(Flee())
    if any(k in t for k in ("pay", "defend", "protect", "property", "bat", "handle")):
        if focus_location:
            actions.append(Investigate(location=focus_location))
    if any(k in t for k in ("police", "call", "report")):
        actions.append(CallContact(contact="police"))

    return AgentDecision(reasoning="heuristic mock grounding", actions=actions)


def decide(llm, prompt: str, world: WorldState, focus_location=None) -> ValidationResult:
    """Produce a validated decision for ``world`` from ``llm`` given ``prompt``."""
    is_loaded = getattr(llm, "is_loaded", lambda: False)()

    if is_loaded:
        grammar = build_grammar()
        raw = llm.generate_decision(prompt, grammar=grammar)
        decision = parse_decision(raw)
    else:
        text = llm.generate(prompt)
        decision = heuristic_decision(text, focus_location=focus_location)

    return ActionValidator(world).validate(decision)
