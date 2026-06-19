"""
Tests for behavioral grounding.

The headline guarantee: whatever the model emits - well-formed, malformed, or
adversarial - the engine only ever receives actions drawn from the verb set and
referencing entities that actually exist in the world. These tests fuzz the
model output and assert that invariant holds.
"""

import json
import random

import pytest

from grounding.actions import VERBS, AgentDecision
from grounding.runtime import decide, heuristic_decision, parse_decision
from grounding.validator import ActionValidator, WorldState


def make_world():
    return WorldState(
        agent_id="student_01",
        agent_location="apartment_1a",
        locations={"apartment_1a", "bakery", "street", "hallway"},
        agents={"student_01", "baker_01", "landlord_01"},
        objects={"brick_01": "apartment_1a", "ledger_01": "bakery"},
    )


# --- schema / vocabulary -------------------------------------------------

def test_schema_lists_all_verbs():
    schema = AgentDecision.model_json_schema()
    text = json.dumps(schema)
    for verb in VERBS:
        assert verb in text


# --- validator: legal actions kept --------------------------------------

def test_valid_actions_are_kept():
    world = make_world()
    decision = AgentDecision(actions=parse_decision(json.dumps({
        "actions": [
            {"verb": "say", "text": "What was that?"},
            {"verb": "move_to", "location": "hallway"},
            {"verb": "pick_up", "object_id": "brick_01"},
            {"verb": "hide"},
        ]
    })).actions)
    result = ActionValidator(world).validate(decision)
    assert [a.verb for a in result.decision.actions] == [
        "say", "move_to", "pick_up", "hide"
    ]
    assert result.rejected == []


# --- validator: each illegal case is rejected ---------------------------

@pytest.mark.parametrize("action,reason_contains", [
    ({"verb": "move_to", "location": "narnia"}, "unknown location"),
    ({"verb": "investigate", "location": "atlantis"}, "unknown location"),
    ({"verb": "pick_up", "object_id": "ghost_item"}, "unknown object"),
    ({"verb": "pick_up", "object_id": "ledger_01"}, "not here"),  # exists, wrong room
    ({"verb": "attack", "target_id": "dragon"}, "unknown target"),
    ({"verb": "attack", "target_id": "student_01"}, "cannot attack self"),
    ({"verb": "call_contact", "contact": "ghostbusters"}, "unknown contact"),
])
def test_illegal_actions_are_rejected(action, reason_contains):
    world = make_world()
    decision = parse_decision(json.dumps({"actions": [action]}))
    result = ActionValidator(world).validate(decision)

    # The illegal action must not survive...
    assert len(result.rejected) == 1
    assert reason_contains in result.rejected[0]["reason"]
    # ...and the agent still gets a legal, bounded decision.
    assert [a.verb for a in result.decision.actions] == ["do_nothing"]


def test_flee_to_unknown_location_is_repaired_not_dropped():
    world = make_world()
    decision = parse_decision(json.dumps({
        "actions": [{"verb": "flee", "to_location": "narnia"}]
    }))
    result = ActionValidator(world).validate(decision)
    assert result.rejected == []
    flee = result.decision.actions[0]
    assert flee.verb == "flee"
    assert flee.to_location is None  # bad destination scrubbed


def test_known_external_contact_is_allowed():
    world = make_world()
    decision = parse_decision(json.dumps({
        "actions": [{"verb": "call_contact", "contact": "police"}]
    }))
    result = ActionValidator(world).validate(decision)
    assert result.rejected == []
    assert result.decision.actions[0].verb == "call_contact"


# --- parsing: never crash on garbage ------------------------------------

@pytest.mark.parametrize("raw", [
    "not json at all",
    "",
    "{}",
    '{"actions": "not a list"}',
    '{"actions": [{"verb": "teleport", "location": "x"}]}',  # invalid verb
    '{"actions": [{"verb": "move_to"}]}',                    # missing field
    "[]",
])
def test_parse_decision_never_raises(raw):
    decision = parse_decision(raw)
    assert isinstance(decision, AgentDecision)


# --- the invariant: fuzz the model, engine never sees an illegal action --

def test_fuzz_validator_never_emits_illegal_action():
    world = make_world()
    validator = ActionValidator(world)
    rng = random.Random(1234)

    junk_locations = ["narnia", "void", "", "APARTMENT_1A", "bakery "]
    junk_objects = ["ghost", "ledger_01", "brick_01", ""]
    junk_targets = ["dragon", "student_01", "baker_01", "nobody"]

    for _ in range(500):
        verb = rng.choice(sorted(VERBS) + ["teleport", "explode"])  # include bogus verbs
        action = {"verb": verb}
        if verb in ("move_to", "investigate"):
            action["location"] = rng.choice(junk_locations + ["bakery", "hallway"])
        elif verb == "pick_up":
            action["object_id"] = rng.choice(junk_objects)
        elif verb == "attack":
            action["target_id"] = rng.choice(junk_targets)
        elif verb == "call_contact":
            action["contact"] = rng.choice(["police", "ghostbusters", "baker_01"])
        elif verb == "say":
            action["text"] = "x"
        elif verb == "flee":
            action["to_location"] = rng.choice(junk_locations + [None])

        decision = parse_decision(json.dumps({"actions": [action]}))
        result = validator.validate(decision)

        for a in result.decision.actions:
            # Only real verbs survive.
            assert a.verb in VERBS
            # Every world reference points at something that exists.
            if a.verb in ("move_to", "investigate"):
                assert world.location_exists(a.location)
            elif a.verb == "pick_up":
                assert world.objects.get(a.object_id) == world.agent_location
            elif a.verb == "attack":
                assert a.target_id in world.agents and a.target_id != world.agent_id
            elif a.verb == "call_contact":
                assert a.contact in world.agents or a.contact in world.contacts
            elif a.verb == "flee" and a.to_location is not None:
                assert world.reachable(world.agent_location, a.to_location)


# --- end-to-end through the mock LLM ------------------------------------

class _MockLLM:
    """Stands in for LLMEngine in mock mode."""
    def is_loaded(self):
        return False

    def generate(self, prompt, **kwargs):
        return "Oh no, I really can't deal with this right now!"


def test_decide_grounds_mock_output_into_valid_actions():
    world = make_world()
    result = decide(_MockLLM(), "A window shattered.", world, focus_location="apartment_1a")
    verbs = [a.verb for a in result.decision.actions]
    assert "say" in verbs
    assert "hide" in verbs  # anxious line -> hide cue
    for a in result.decision.actions:
        assert a.verb in VERBS


def test_heuristic_drops_focus_when_location_unknown():
    """An NPC told to investigate a non-existent focus location is not let through."""
    world = WorldState(
        agent_id="x", agent_location="room", locations={"room"},
        agents={"x"}, objects={},
    )
    decision = heuristic_decision("Someone will pay for this property damage!",
                                  focus_location="nonexistent_room")
    result = ActionValidator(world).validate(decision)
    assert all(
        not (a.verb == "investigate" and a.location == "nonexistent_room")
        for a in result.decision.actions
    )
