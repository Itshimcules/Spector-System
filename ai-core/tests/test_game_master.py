import json
import os
import pytest
from orchestration.game_master import GameMaster

AI_CORE = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture
def config_files(tmp_path):
    settings = {
        "api": {"host": "0.0.0.0", "port": 8000},
        "models": {"base_model_path": "models/base", "lora_directory": "models/loras"},
    }
    agents_yaml = """
agents:
  - id: "baker_01"
    name: "Martha Quinn"
    archetype: "grumpy_baker"
    lora_adapter: "baker.lora"
    personality_traits: [irritable, perfectionist]
    backstory: "Runs the corner bakery for 30 years."
    current_location: "bakery"

  - id: "student_01"
    name: "Emily Chen"
    archetype: "anxious_student"
    lora_adapter: "student.lora"
    personality_traits: [nervous, studious]
    backstory: "Pre-med student cramming for finals."
    current_location: "apartment_1a"

game_master:
  wake_conditions:
    loud_noise:
      radius: 15.0
      wake_probability: 0.9
    property_damage:
      radius: 10.0
      wake_probability: 0.8
    violence:
      radius: 20.0
      wake_probability: 1.0
"""
    settings_path = tmp_path / "settings.json"
    agents_path = tmp_path / "agents.yaml"
    settings_path.write_text(json.dumps(settings))
    agents_path.write_text(agents_yaml)
    return str(settings_path), str(agents_path)


def test_game_master_init(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    assert gm.agents_config is not None
    assert len(gm.agents_config["agents"]) == 2


def test_semantic_radius_known_event(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    assert gm.calculate_semantic_radius({"event_type": "property_damage"}) == 10.0
    assert gm.calculate_semantic_radius({"event_type": "loud_noise"}) == 15.0
    assert gm.calculate_semantic_radius({"event_type": "violence"}) == 20.0


def test_semantic_radius_unknown_event_uses_noise_level(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    radius = gm.calculate_semantic_radius({"event_type": "unknown", "noise_level": 80})
    assert radius == 8.0


def test_semantic_radius_unknown_event_minimum(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    radius = gm.calculate_semantic_radius({"event_type": "unknown", "noise_level": 0})
    assert radius == 5.0


def test_get_affected_agents_returns_list(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    affected = gm.get_affected_agents({"event_type": "property_damage", "location": "bakery"})
    assert isinstance(affected, list)


def test_process_event_structure(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    event = {
        "event_type": "property_damage",
        "action": "break_glass",
        "location": "bakery",
        "noise_level": 90,
        "event_description": "A window has been shattered.",
    }
    response = gm.process_event(event)
    assert "event_id" in response
    assert "timestamp" in response
    assert "affected_agents" in response
    assert "agent_reactions" in response
    assert isinstance(response["agent_reactions"], list)


def test_process_event_increments_history(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    event = {"event_type": "loud_noise", "location": "street"}
    gm.process_event(event)
    gm.process_event(event)
    assert len(gm.event_history) == 2
    assert gm.event_history[0]["event"] == event


def test_process_event_id_increments(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    event = {"event_type": "loud_noise", "location": "street"}
    r1 = gm.process_event(event)
    r2 = gm.process_event(event)
    assert r2["event_id"] == r1["event_id"] + 1


def test_generate_prompt_includes_agent_name(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    agent = {"name": "Test NPC", "archetype": "guard", "personality_traits": ["brave"], "backstory": "A guard."}
    event = {"event_description": "Fire alarm triggered.", "location": "lobby"}
    prompt = gm._generate_prompt(agent, event)
    assert "Test NPC" in prompt
    assert "Fire alarm triggered." in prompt


def test_get_agent_schedule_missing_schedule(config_files):
    settings_path, agents_path = config_files
    gm = GameMaster(config_path=settings_path, agents_path=agents_path)
    result = gm.get_agent_schedule("baker_01", "10:00")
    assert result is None or isinstance(result, dict)


def test_resolve_config_path_returns_existing(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text("{}")
    assert GameMaster._resolve_config_path(str(settings)) == str(settings)


def test_resolve_config_path_falls_back_to_example(tmp_path):
    example = tmp_path / "settings.example.json"
    example.write_text("{}")
    resolved = GameMaster._resolve_config_path(str(tmp_path / "settings.json"))
    assert resolved == str(example)


def test_resolve_config_path_raises_when_nothing_present(tmp_path):
    with pytest.raises(FileNotFoundError):
        GameMaster._resolve_config_path(str(tmp_path / "settings.json"))


def test_default_init_works_from_ai_core(monkeypatch):
    """A fresh clone (no settings.json) must still construct via the example."""
    monkeypatch.chdir(AI_CORE)
    gm = GameMaster()
    assert gm.agents_config["agents"]
    # Every agent's adapter name must match an asset on disk (archetype-named).
    for agent in gm.agents_config["agents"]:
        assert agent["lora_adapter"].endswith(".lora")
