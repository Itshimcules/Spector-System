"""
HTTP-level smoke test for the FastAPI app.

Guarded with importorskip so the lightweight CI (pyyaml + pytest only) skips
it, while a full install (core requirements include fastapi + httpx) exercises
the real endpoints. The /event test is the HTTP-level guard for the headline
"throw a brick" demo returning 200 with generated reactions.
"""

import os
import sys
from pathlib import Path

import pytest

AI_CORE = Path(__file__).resolve().parents[1]

BROKEN_WINDOW = {
    "event_type": "property_damage",
    "action": "break_glass",
    "location": "apartment_1a",
    "noise_level": 90,
    "event_description": "A window has been shattered by a thrown brick.",
}


@pytest.fixture
def client(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    # Service singletons resolve config/models/db via paths relative to ai-core.
    monkeypatch.chdir(AI_CORE)
    sys.modules.pop("main_api", None)
    import main_api
    from fastapi.testclient import TestClient

    return TestClient(main_api.app)


def test_root_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "service" in resp.json()


def test_list_agents(client):
    resp = client.get("/agents")
    assert resp.status_code == 200
    agents = resp.json()["agents"]
    assert agents
    for agent in agents:
        assert agent["lora_adapter"].endswith(".lora")


def test_event_returns_generated_reactions(client):
    resp = client.post("/event", json=BROKEN_WINDOW)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["affected_agents"]
    for reaction in body["agent_reactions"]:
        assert reaction["generated_response"]


def test_event_reactions_carry_validated_decisions(client):
    from grounding.actions import VERBS

    resp = client.post("/event", json=BROKEN_WINDOW)
    body = resp.json()
    for reaction in body["agent_reactions"]:
        decision = reaction["decision"]
        assert decision["actions"], "every reaction must yield at least one action"
        for action in decision["actions"]:
            assert action["verb"] in VERBS


def test_dialogue_unknown_npc_returns_404(client):
    resp = client.post(
        "/dialogue", json={"npc_id": "ghost_99", "player_message": "Hi?"}
    )
    assert resp.status_code == 404
