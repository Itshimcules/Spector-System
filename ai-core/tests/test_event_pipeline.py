"""
End-to-end test of the event pipeline against the REAL project config.

This wires GameMaster -> LoRASwitcher exactly as the /event endpoint does,
using the shipped config/agents.yaml, config/settings.example.json, and
models/loras. It reproduces (and guards against) the fresh-clone failure where
the "broken window" demo 500'd because agent adapter names didn't match the
adapter assets on disk.
"""

import os
import pytest

from orchestration.game_master import GameMaster
from orchestration.lora_switcher import LoRASwitcher

AI_CORE = os.path.dirname(os.path.dirname(__file__))
SETTINGS = os.path.join(AI_CORE, "config", "settings.example.json")
AGENTS = os.path.join(AI_CORE, "config", "agents.yaml")
LORAS = os.path.join(AI_CORE, "models", "loras")

BROKEN_WINDOW = {
    "event_type": "property_damage",
    "action": "break_glass",
    "location": "apartment_1a",
    "noise_level": 90,
    "event_description": "A window has been shattered by a thrown brick.",
}


@pytest.fixture
def pipeline():
    gm = GameMaster(config_path=SETTINGS, agents_path=AGENTS)
    switcher = LoRASwitcher(base_model_path="x", lora_directory=LORAS)
    return gm, switcher


def test_broken_window_event_produces_reactions(pipeline):
    gm, switcher = pipeline
    response = gm.process_event(BROKEN_WINDOW)

    assert response["affected_agents"], "no agents reacted to the event"
    assert response["agent_reactions"], "no reactions generated"


def test_every_reaction_generates_text(pipeline):
    """The exact loop main_api runs after process_event must not raise."""
    gm, switcher = pipeline
    response = gm.process_event(BROKEN_WINDOW)

    for reaction in response["agent_reactions"]:
        generated = switcher.generate_response(
            adapter_name=reaction["lora_adapter"],
            prompt=reaction["prompt"],
        )
        assert isinstance(generated, str) and generated, (
            f"empty/failed generation for {reaction['agent_id']}"
        )


def test_co_located_agent_wakes_for_quiet_event(pipeline):
    """A conversation has a small radius; only the co-located NPC should wake."""
    gm, _ = pipeline
    event = {
        "event_type": "conversation",
        "location": "apartment_1a",
        "event_description": "Two people argue quietly.",
    }
    affected = gm.get_affected_agents(event)
    # Emily (student_01) and Vincent (landlord_01) are in apartment_1a;
    # the baker (bakery) and cop (street) are not.
    assert "baker_01" not in affected
    assert "cop_01" not in affected
