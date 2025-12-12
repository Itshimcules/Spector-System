"""
LLM Inference Engine
Handles model loading and text generation using llama.cpp
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMEngine:
    """
    Wrapper for LLM inference using llama-cpp-python
    Falls back to mock responses if model is not available
    """
    
    def __init__(self, model_path: str = None, use_gpu: bool = True):
        self.model_path = model_path
        self.model = None
        self.use_mock = True
        
        if model_path and Path(model_path).exists():
            try:
                from llama_cpp import Llama
                
                logger.info(f"Loading model from {model_path}")
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_gpu_layers=-1 if use_gpu else 0,
                    verbose=False
                )
                self.use_mock = False
                logger.info("✓ LLM model loaded successfully")
            except ImportError:
                logger.warning("llama-cpp-python not installed, using mock responses")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                logger.warning("Falling back to mock responses")
        else:
            logger.info("No model specified, using mock responses")
    
    def generate(self, 
                 prompt: str, 
                 max_tokens: int = 100,
                 temperature: float = 0.7,
                 stop: list = None) -> str:
        """Generate text completion"""
        
        if self.use_mock:
            return self._mock_generate(prompt, max_tokens)
        
        try:
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or ["\n\n", "###"],
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return self._mock_generate(prompt, max_tokens)
    
    def _mock_generate(self, prompt: str, max_tokens: int) -> str:
        """Generate mock response for testing"""
        # Extract character traits from prompt
        if "grumpy" in prompt.lower() or "baker" in prompt.lower():
            return "I don't have time for this nonsense!"
        elif "cop" in prompt.lower() or "opportunistic" in prompt.lower():
            return "Looks like we've got a situation here. What's it worth to you?"
        elif "anxious" in prompt.lower() or "student" in prompt.lower():
            return "Oh no, I really can't deal with this right now!"
        elif "landlord" in prompt.lower() or "vigilante" in prompt.lower():
            return "Someone's going to pay for this damage to my property."
        else:
            return "I need to respond to this situation carefully."
    
    def chat(self, messages: list, max_tokens: int = 100) -> str:
        """Chat completion with message history"""
        # Convert messages to prompt format
        prompt = self._format_chat_prompt(messages)
        return self.generate(prompt, max_tokens)
    
    def _format_chat_prompt(self, messages: list) -> str:
        """Format chat messages into prompt"""
        prompt = ""
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt += f"{content}\n\n"
            elif role == 'user':
                prompt += f"Human: {content}\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n"
        
        prompt += "Assistant:"
        return prompt
    
    def is_loaded(self) -> bool:
        """Check if real model is loaded"""
        return not self.use_mock
    
    def get_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            'model_path': self.model_path,
            'loaded': self.is_loaded(),
            'using_mock': self.use_mock
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test with mock
    engine = LLMEngine()
    
    response = engine.generate(
        "You are Martha Quinn, a grumpy baker. Someone just broke a window. How do you react?",
        max_tokens=50
    )
    
    print(f"Response: {response}")
    print(f"Model info: {engine.get_info()}")
