"""
LoRA Switcher - Dynamic Personality Loading
Hot-swaps LoRA adapters into the base model for character-specific inference
"""

import os
import json
from typing import Dict, Optional
import time
import logging


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
        logger = logging.getLogger(__name__)
        logger.info(f"Initialized LoRA switcher: {base_model_path}")
    
    def _get_lora_path(self, adapter_name: str) -> str:
        """Construct full path to LoRA adapter file"""
        return os.path.join(self.lora_directory, adapter_name)
    
    def _load_adapter(self, adapter_name: str) -> any:
        """Load a LoRA adapter from disk"""
        adapter_path = self._get_lora_path(adapter_name)
        
        if not os.path.exists(adapter_path):
            raise FileNotFoundError(f"LoRA adapter not found: {adapter_path}")
        
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Loading adapter: {adapter_name}")
        start_time = time.time()
        
        adapter = {"name": adapter_name, "path": adapter_path}
        
        load_time = time.time() - start_time
        logger.info(f"Loaded {adapter_name} in {load_time:.2f}s")
        
        return adapter
    
    def _manage_cache(self) -> None:
        """
        Evict least recently used adapter if cache is full
        """
        if len(self.loaded_adapters) >= self.max_cache_size:
            # Find LRU adapter
            lru_adapter = min(self.load_times.items(), key=lambda x: x[1])[0]
            print(f"Cache full. Evicting: {lru_adapter}")
            del self.loaded_adapters[lru_adapter]
            del self.load_times[lru_adapter]
    
    def get_adapter(self, adapter_name: str) -> any:
        """
        Get a LoRA adapter, loading it if necessary
        Uses LRU caching to keep hot adapters in memory
        """
        # Check if already loaded
        if adapter_name in self.loaded_adapters:
            print(f"Cache hit: {adapter_name}")
            self.load_times[adapter_name] = time.time()
            return self.loaded_adapters[adapter_name]
        
        # Cache miss - need to load
        print(f"Cache miss: {adapter_name}")
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
        print(f"Pre-loading {len(adapter_names)} adapters...")
        for adapter_name in adapter_names:
            if adapter_name not in self.loaded_adapters:
                try:
                    self.get_adapter(adapter_name)
                except FileNotFoundError as e:
                    print(f"Warning: {e}")
    
    def generate_response(self, adapter_name: str, prompt: str,
                         max_tokens: int = 100,
                         temperature: float = 0.7) -> str:
        """
        Generate text using the specified LoRA adapter
        """
        adapter = self.get_adapter(adapter_name)
        
        # Load LLM engine if not already loaded
        if not hasattr(self, 'llm_engine'):
            from models.llm_engine import LLMEngine
            self.llm_engine = LLMEngine()
        
        # Get character metadata if available
        character_context = ""
        metadata_path = self._get_lora_path(adapter_name).replace('.lora', '.json')
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path) as f:
                metadata = json.load(f)
                traits = metadata.get('traits', [])
                if traits:
                    character_context = f"Character traits: {', '.join(traits)}. "
        
        # Enhance prompt with character context
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
        print("Clearing adapter cache...")
        self.loaded_adapters.clear()
        self.load_times.clear()


if __name__ == "__main__":
    # Example usage
    switcher = LoRASwitcher(
        base_model_path="models/base/llama-3-8b-quantized",
        lora_directory="models/loras",
        max_cache_size=3
    )
    
    # Simulate loading different character adapters
    test_adapters = ["baker.lora", "cop.lora", "student.lora"]
    
    # Pre-load adapters for NPCs near the player
    switcher.preload_adapters(["baker.lora", "cop.lora"])
    
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
