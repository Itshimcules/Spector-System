"""
LoRA Switcher - Dynamic Personality Loading
Hot-swaps LoRA adapters into the base model for character-specific inference.

Degrades gracefully, matching the rest of the framework: when a character's
trained ``.lora`` weights are not present on disk (the common case during
development, since weights are large and git-ignored), the switcher loads the
adapter's ``.json`` metadata only and serves mock responses. An adapter is
considered missing - and only then raises - when neither the weights nor the
metadata sidecar can be found.
"""

import os
import json
from typing import Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)


class LoRASwitcher:
    """
    Manages dynamic loading/unloading of LoRA adapters
    Enables one base model to portray hundreds of characters
    """

    def __init__(self, base_model_path: str, lora_directory: str,
                 max_cache_size: int = 3):
        self.base_model_path = base_model_path
        self.lora_directory = lora_directory
        self.max_cache_size = max_cache_size

        # Cache of currently loaded adapters
        self.loaded_adapters: Dict[str, any] = {}
        self.load_times: Dict[str, float] = {}

        self.base_model = None
        logger.info(f"Initialized LoRA switcher: {base_model_path}")

    def _get_lora_path(self, adapter_name: str) -> str:
        """Construct full path to LoRA adapter weights file"""
        return os.path.join(self.lora_directory, adapter_name)

    def _get_metadata_path(self, adapter_name: str) -> str:
        """Construct full path to the adapter's JSON metadata sidecar"""
        base = adapter_name[:-5] if adapter_name.endswith(".lora") else adapter_name
        return os.path.join(self.lora_directory, f"{base}.json")

    def _load_adapter(self, adapter_name: str) -> dict:
        """
        Load a LoRA adapter from disk.

        Resolution order:
          * trained weights (``<name>.lora``) present -> real adapter
          * only metadata (``<name>.json``) present   -> mock adapter
          * neither present                            -> FileNotFoundError
        """
        weights_path = self._get_lora_path(adapter_name)
        metadata_path = self._get_metadata_path(adapter_name)

        has_weights = os.path.exists(weights_path)
        has_metadata = os.path.exists(metadata_path)

        if not has_weights and not has_metadata:
            raise FileNotFoundError(
                f"LoRA adapter not found: no weights at '{weights_path}' "
                f"and no metadata at '{metadata_path}'"
            )

        metadata = {}
        if has_metadata:
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not read metadata for {adapter_name}: {e}")

        start_time = time.time()
        is_mock = not has_weights
        adapter = {
            "name": adapter_name,
            "path": weights_path if has_weights else None,
            "metadata_path": metadata_path if has_metadata else None,
            "metadata": metadata,
            "is_mock": is_mock,
        }

        load_time = time.time() - start_time
        mode = "metadata-only (mock)" if is_mock else "weights"
        logger.info(f"Loaded {adapter_name} [{mode}] in {load_time:.3f}s")

        return adapter

    def _manage_cache(self) -> None:
        """
        Evict least recently used adapter if cache is full
        """
        if len(self.loaded_adapters) >= self.max_cache_size:
            # Find LRU adapter
            lru_adapter = min(self.load_times.items(), key=lambda x: x[1])[0]
            logger.info(f"Cache full. Evicting: {lru_adapter}")
            del self.loaded_adapters[lru_adapter]
            del self.load_times[lru_adapter]

    def get_adapter(self, adapter_name: str) -> any:
        """
        Get a LoRA adapter, loading it if necessary
        Uses LRU caching to keep hot adapters in memory
        """
        # Check if already loaded
        if adapter_name in self.loaded_adapters:
            logger.debug(f"Cache hit: {adapter_name}")
            self.load_times[adapter_name] = time.time()
            return self.loaded_adapters[adapter_name]

        # Cache miss - need to load
        logger.debug(f"Cache miss: {adapter_name}")
        self._manage_cache()

        adapter = self._load_adapter(adapter_name)
        self.loaded_adapters[adapter_name] = adapter
        self.load_times[adapter_name] = time.time()

        return adapter

    def preload_adapters(self, adapter_names: list[str]) -> None:
        """
        Pre-fetch adapters into cache
        Useful for predictive loading (e.g., when player approaches NPCs)
        """
        logger.info(f"Pre-loading {len(adapter_names)} adapters...")
        for adapter_name in adapter_names:
            if adapter_name not in self.loaded_adapters:
                try:
                    self.get_adapter(adapter_name)
                except FileNotFoundError as e:
                    logger.warning(str(e))

    def generate_response(self, adapter_name: str, prompt: str,
                         max_tokens: int = 100,
                         temperature: float = 0.7) -> str:
        """
        Generate text using the specified LoRA adapter.

        Works whether the adapter is backed by real weights or is a
        metadata-only mock; the LLM engine itself falls back to mock
        generation when no base model is loaded.
        """
        adapter = self.get_adapter(adapter_name)

        # Load LLM engine if not already loaded
        if not hasattr(self, 'llm_engine'):
            from models.llm_engine import LLMEngine
            self.llm_engine = LLMEngine()

        # Enrich the prompt with character traits from the adapter metadata
        character_context = ""
        traits = (adapter.get('metadata') or {}).get('traits', [])
        if traits:
            character_context = f"Character traits: {', '.join(traits)}. "

        enhanced_prompt = f"{character_context}{prompt}"

        # Generate response
        response = self.llm_engine.generate(
            enhanced_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response

    def get_cache_status(self) -> Dict[str, any]:
        """Get current cache statistics"""
        return {
            'loaded_adapters': list(self.loaded_adapters.keys()),
            'cache_size': len(self.loaded_adapters),
            'max_cache_size': self.max_cache_size,
            'utilization': len(self.loaded_adapters) / self.max_cache_size
        }

    def clear_cache(self) -> None:
        """Clear all loaded adapters from cache"""
        logger.info("Clearing adapter cache...")
        self.loaded_adapters.clear()
        self.load_times.clear()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    switcher = LoRASwitcher(
        base_model_path="models/base/llama-3-8b-quantized",
        lora_directory="models/loras",
        max_cache_size=3
    )

    # Simulate loading different character adapters (metadata-only mocks ship
    # in the repo; trained .lora weights are added later).
    test_adapters = ["grumpy_baker.lora", "corrupt_cop.lora", "anxious_student.lora"]

    # Pre-load adapters for NPCs near the player
    switcher.preload_adapters(["grumpy_baker.lora", "corrupt_cop.lora"])

    # Generate responses from different characters
    prompt = "You hear a loud crash and breaking glass."

    for adapter in test_adapters:
        print(f"\n--- Using {adapter} ---")
        try:
            response = switcher.generate_response(adapter, prompt)
            print(response)
        except FileNotFoundError as e:
            print(f"Error: {e}")

    # Check cache status
    status = switcher.get_cache_status()
    print(f"\nCache Status: {json.dumps(status, indent=2)}")
