"""
Action validation - the "cannot break game state" guarantee.

Constrained decoding guarantees an action is *structurally* legal (a real verb
with well-typed args). It does NOT guarantee the action makes sense in the world:
the model can still tell an NPC to walk into a room that doesn't exist, pick up
an object that isn't there, or attack a character who left. The validator is the
gate that turns generated intent into something the engine can safely execute.

Every action is checked against a snapshot of world state. Illegal actions are
dropped or repaired (never executed), and the reason is recorded for QA. If an
agent is left with nothing it can legally do, it falls back to ``do_nothing`` so
the engine always receives a valid, bounded decision.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .actions import AgentDecision, DoNothing

# External parties an NPC may "call" even though they aren't simulated agents.
DEFAULT_CONTACTS = {"police", "emergency_services"}


@dataclass
class WorldState:
    """A read-only snapshot of what the validator needs to know about the world."""

    agent_id: str
    agent_location: str
    locations: Set[str]
    agents: Set[str]
    objects: Dict[str, str]  # object_id -> current location
    contacts: Set[str] = field(default_factory=lambda: set(DEFAULT_CONTACTS))
    # Optional adjacency map; when absent, any known location is reachable.
    adjacency: Optional[Dict[str, Set[str]]] = None

    def location_exists(self, loc: str) -> bool:
        return loc in self.locations

    def reachable(self, src: str, dst: str) -> bool:
        if dst not in self.locations:
            return False
        if not self.adjacency:
            return True
        return src == dst or dst in self.adjacency.get(src, set())

    @classmethod
    def from_sources(cls, agents_config: dict, rag_engine, agent_id: str) -> "WorldState":
        """Build a snapshot from the agents.yaml config and the RAG world objects."""
        agents: Set[str] = set()
        locations: Set[str] = set()
        agent_location = "unknown"

        for agent in (agents_config or {}).get("agents", []):
            agents.add(agent["id"])
            loc = agent.get("current_location")
            if not loc and agent.get("schedule"):
                loc = agent["schedule"][0].get("location")
            if loc:
                locations.add(loc)
            if agent["id"] == agent_id and loc:
                agent_location = loc

        objects: Dict[str, str] = {}
        if rag_engine is not None and hasattr(rag_engine, "all_objects"):
            try:
                for obj in rag_engine.all_objects():
                    loc = obj.get("current_location")
                    objects[obj["id"]] = loc
                    if loc:
                        locations.add(loc)
            except Exception:
                pass

        return cls(
            agent_id=agent_id,
            agent_location=agent_location,
            locations=locations,
            agents=agents,
            objects=objects,
        )


@dataclass
class ValidationResult:
    decision: AgentDecision
    rejected: List[Dict[str, Any]]


class ActionValidator:
    """Validates (and where sensible repairs) an AgentDecision against world state."""

    def __init__(self, world: WorldState):
        self.w = world

    def validate(self, decision: AgentDecision) -> ValidationResult:
        kept = []
        rejected: List[Dict[str, Any]] = []

        for action in decision.actions:
            ok, reason, repaired = self._check(action)
            if ok:
                kept.append(repaired if repaired is not None else action)
            else:
                rejected.append({"action": action.model_dump(), "reason": reason})

        # The engine must always get a legal, bounded decision.
        if not kept:
            kept.append(DoNothing())

        return ValidationResult(
            decision=AgentDecision(reasoning=decision.reasoning, actions=kept),
            rejected=rejected,
        )

    def _check(self, a) -> Tuple[bool, str, Optional[Any]]:
        verb = a.verb

        # Always safe - no world references.
        if verb in ("say", "hide", "do_nothing"):
            return True, "", None

        if verb == "move_to":
            if not self.w.location_exists(a.location):
                return False, f"unknown location '{a.location}'", None
            if not self.w.reachable(self.w.agent_location, a.location):
                return False, f"location '{a.location}' not reachable", None
            return True, "", None

        if verb == "investigate":
            if not self.w.location_exists(a.location):
                return False, f"unknown location '{a.location}'", None
            return True, "", None

        if verb == "pick_up":
            loc = self.w.objects.get(a.object_id)
            if loc is None:
                return False, f"unknown object '{a.object_id}'", None
            if loc != self.w.agent_location:
                return False, f"object '{a.object_id}' is not here", None
            return True, "", None

        if verb == "flee":
            if a.to_location is not None and not self.w.reachable(
                self.w.agent_location, a.to_location
            ):
                # Repair: drop the bad destination, flee in general.
                return True, "", a.model_copy(update={"to_location": None})
            return True, "", None

        if verb == "call_contact":
            if a.contact in self.w.agents or a.contact in self.w.contacts:
                return True, "", None
            return False, f"unknown contact '{a.contact}'", None

        if verb == "attack":
            if a.target_id == self.w.agent_id:
                return False, "cannot attack self", None
            if a.target_id not in self.w.agents:
                return False, f"unknown target '{a.target_id}'", None
            return True, "", None

        return False, f"unknown verb '{verb}'", None
