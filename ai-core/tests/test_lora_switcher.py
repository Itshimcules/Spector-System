import time
import pytest
from orchestration.lora_switcher import LoRASwitcher


def make_switcher(max_cache: int = 2) -> LoRASwitcher:
    return LoRASwitcher(
        base_model_path="models/base/llama-3-8b",
        lora_directory="/tmp/nonexistent_loras",
        max_cache_size=max_cache,
    )


def test_cache_status_starts_empty():
    switcher = make_switcher()
    status = switcher.get_cache_status()
    assert status["cache_size"] == 0
    assert status["max_cache_size"] == 2
    assert status["loaded_adapters"] == []
    assert status["utilization"] == 0.0


def test_clear_cache_empties_loaded_adapters():
    switcher = make_switcher()
    switcher.loaded_adapters["a.lora"] = {"name": "a"}
    switcher.load_times["a.lora"] = time.time()
    switcher.clear_cache()
    assert switcher.get_cache_status()["cache_size"] == 0
    assert "a.lora" not in switcher.loaded_adapters


def test_lru_eviction_removes_oldest():
    switcher = make_switcher(max_cache=2)
    switcher.loaded_adapters["a.lora"] = {}
    switcher.load_times["a.lora"] = 1.0
    switcher.loaded_adapters["b.lora"] = {}
    switcher.load_times["b.lora"] = 2.0
    switcher._manage_cache()
    assert "a.lora" not in switcher.loaded_adapters
    assert "b.lora" in switcher.loaded_adapters


def test_lru_no_eviction_when_cache_has_space():
    switcher = make_switcher(max_cache=3)
    switcher.loaded_adapters["a.lora"] = {}
    switcher.load_times["a.lora"] = 1.0
    switcher.loaded_adapters["b.lora"] = {}
    switcher.load_times["b.lora"] = 2.0
    switcher._manage_cache()
    assert len(switcher.loaded_adapters) == 2


def test_get_adapter_raises_for_missing_file():
    switcher = make_switcher()
    with pytest.raises(FileNotFoundError):
        switcher.get_adapter("nonexistent.lora")


def test_cache_hit_returns_cached_adapter():
    switcher = make_switcher()
    fake = {"name": "cached_adapter"}
    switcher.loaded_adapters["cached.lora"] = fake
    switcher.load_times["cached.lora"] = time.time()
    result = switcher.get_adapter("cached.lora")
    assert result is fake


def test_utilization_calculation():
    switcher = make_switcher(max_cache=4)
    switcher.loaded_adapters["a.lora"] = {}
    switcher.load_times["a.lora"] = time.time()
    switcher.loaded_adapters["b.lora"] = {}
    switcher.load_times["b.lora"] = time.time()
    status = switcher.get_cache_status()
    assert status["utilization"] == 0.5
