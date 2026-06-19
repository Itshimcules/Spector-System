"""
Integration tests for LoRASwitcher against real and synthetic adapter assets.

These cover the graceful mock fallback that lets the framework run with no
model downloads: a metadata-only adapter (`.json` present, `.lora` weights
absent) must load and generate, while a genuinely absent adapter still raises.
"""

import json
import os
import yaml
import pytest

from orchestration.lora_switcher import LoRASwitcher

AI_CORE = os.path.dirname(os.path.dirname(__file__))
REAL_LORAS = os.path.join(AI_CORE, "models", "loras")
AGENTS_YAML = os.path.join(AI_CORE, "config", "agents.yaml")


def test_metadata_only_adapter_loads_as_mock(tmp_path):
    """An adapter with only a .json sidecar loads as a mock, not an error."""
    (tmp_path / "ghost.json").write_text(json.dumps({"traits": ["spooky"]}))
    switcher = LoRASwitcher(base_model_path="x", lora_directory=str(tmp_path))

    adapter = switcher.get_adapter("ghost.lora")
    assert adapter["is_mock"] is True
    assert adapter["metadata"]["traits"] == ["spooky"]


def test_metadata_only_adapter_generates_without_weights(tmp_path):
    (tmp_path / "ghost.json").write_text(json.dumps({"traits": ["grumpy"]}))
    switcher = LoRASwitcher(base_model_path="x", lora_directory=str(tmp_path))

    response = switcher.generate_response("ghost.lora", "Someone broke a window.")
    assert isinstance(response, str)
    assert response  # non-empty mock response


def test_real_weights_take_precedence_over_mock(tmp_path):
    (tmp_path / "hero.json").write_text(json.dumps({"traits": ["brave"]}))
    (tmp_path / "hero.lora").write_text("fake weights")
    switcher = LoRASwitcher(base_model_path="x", lora_directory=str(tmp_path))

    adapter = switcher.get_adapter("hero.lora")
    assert adapter["is_mock"] is False
    assert adapter["path"].endswith("hero.lora")


def test_truly_missing_adapter_still_raises(tmp_path):
    """Neither weights nor metadata -> genuinely missing -> raises."""
    switcher = LoRASwitcher(base_model_path="x", lora_directory=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        switcher.get_adapter("does_not_exist.lora")


def test_shipped_agent_adapters_all_resolve():
    """
    Regression guard: every lora_adapter referenced in the real agents.yaml
    must resolve against the real loras directory (this is exactly what the
    /event endpoint does, and what used to 500 in a fresh clone).
    """
    with open(AGENTS_YAML) as f:
        agents = yaml.safe_load(f)["agents"]

    switcher = LoRASwitcher(base_model_path="x", lora_directory=REAL_LORAS)

    for agent in agents:
        adapter_name = agent["lora_adapter"]
        adapter = switcher.get_adapter(adapter_name)
        assert adapter["metadata"].get("traits"), (
            f"{adapter_name} has no traits metadata"
        )
        response = switcher.generate_response(adapter_name, "A window shattered.")
        assert response, f"{adapter_name} produced an empty response"
