# Contributing to Project Spector

Thank you for your interest in contributing to Project Spector! This document provides guidelines for contributing to the project.

## How to Contribute

### 1. Training New Character LoRAs

To add a new NPC personality:

1. **Prepare Training Data**: Create a JSONL file with character dialogue examples
   ```jsonl
   {"prompt": "Player: Hello!", "completion": "Grumpy response appropriate for character"}
   ```

2. **Train the Adapter**: Use the training script
   ```bash
   cd tools
   ./train_lora.sh my_character data/my_character.jsonl
   ```

3. **Add to Configuration**: Update `ai-core/config/agents.yaml`
   ```yaml
   - id: "my_character_01"
     name: "Character Name"
     archetype: "my_character"
     lora_adapter: "my_character.lora"
   ```

### 2. Optimizing RAG Pipeline

Improvements to vector search performance are always welcome:

- Better embedding models for specific domains
- Query optimization for SQLite-vec
- Memory importance scoring algorithms
- Episodic memory pruning strategies

### 3. Extending the Game Master

The Concordia pattern can be enhanced with:

- More sophisticated event radius calculations
- Agent scheduling and routine systems
- Cross-agent relationship dynamics
- Emergent narrative detection

### 4. Unreal Engine Integration

- Blueprint examples for common interactions
- C++ optimizations for API calls
- Audio streaming for TTS
- Predictive LoRA pre-loading

## Code Style

- **Python**: Follow PEP 8, use type hints
- **C++**: Follow Unreal Engine coding standards
- **Blueprints**: Clear naming, organized folders

## Testing

Before submitting:

1. Test AI backend: `python ai-core/main_api.py`
2. Verify endpoints with curl or Postman
3. Check Unreal integration if applicable

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Questions?

Open an issue for discussion before starting major work.

---

**Remember**: The goal is emergent, believable characters—not perfect AI responses.
