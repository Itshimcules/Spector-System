# AI Model Integration Guide

## Quick Start

All AI components are now implemented with intelligent fallbacks. The system works in **mock mode** by default and will automatically upgrade to real models when available.

---

## Current Status

✅ **Working Now (Mock Mode)**
- LLM inference with character-aware responses
- Speech-to-text transcription (placeholder)
- Text-to-speech synthesis (silent WAV generation)
- LoRA adapter loading and caching
- All 4 character personalities defined

⏳ **Requires Model Files**
- Actual LLM inference (need model weights)
- Real voice synthesis (need Whisper & Piper)
- Vector embeddings (optional enhancement)

---

## Installation Options

### Option 1: Mock Mode (Current - No Downloads)

Everything works now for development:

```bash
cd ai-core
python3 orchestration/lora_switcher.py  # ✓ Works with mocks
python3 models/llm_engine.py            # ✓ Character responses
python3 voice/stt_whisper.py            # ✓ Mock transcription
python3 voice/tts_piper.py              # ✓ Generates WAV files
```

### Option 2: Add LLM Model (4GB download)

For actual text generation:

```bash
# Install llama-cpp-python
pip install llama-cpp-python

# Download a quantized model
cd tools
python3 download_models.py llama-3-8b-instruct-gguf

# Test it
cd ../ai-core
python3 models/llm_engine.py
```

### Option 3: Add Voice Services

For real speech:

```bash
# Whisper STT
pip install openai-whisper
# Model auto-downloads on first use

# Piper TTS
# Install via system package manager:
# Ubuntu: apt install piper
# Or download from: https://github.com/rhasspy/piper
```

---

## Character Personalities

Four LoRA adapters created with distinct personalities:

| Character | Adapter File | Traits |
|-----------|-------------|--------|
| Martha Quinn | `grumpy_baker.lora` | Irritable, perfectionist |
| Officer Martinez | `corrupt_cop.lora` | Cynical, opportunistic |
| Emily Chen | `anxious_student.lora` | Nervous, conflict-averse |
| Vincent Russo | `vigilante_landlord.lora` | Protective, aggressive |

**Location**: `ai-core/models/loras/`

Each adapter includes:
- `.lora` file (personality definition)
- `.json` metadata (traits, character info)

---

## Testing

### Test LLM Engine

```bash
cd ai-core
python3 models/llm_engine.py
```

**Expected Output**:
```
INFO:__main__:No model specified, using mock responses
Response: I don't have time for this nonsense!
Model info: {'model_path': None, 'loaded': False, 'using_mock': True}
```

### Test LoRA Switcher with LLM

```python
from orchestration.lora_switcher import LoRASwitcher

switcher = LoRASwitcher(
    base_model_path="models/base/model.gguf",  # Optional
    lora_directory="models/loras"
)

response = switcher.generate_response(
    "grumpy_baker.lora",
    "Someone just broke your window. How do you react?"
)

print(response)
# Output: Character-specific response based on traits
```

### Test Voice Services

```bash
# STT
cd ai-core
python3 voice/stt_whisper.py
# Output: Mock transcription (or real if Whisper installed)

# TTS
python3 voice/tts_piper.py
# Output: Generates /tmp/test_tts.wav
```

---

## API Integration

Services auto-initialize in `main_api.py`:

```python
# In main_api.py - already integrated
game_master = GameMaster()
lora_switcher = LoRASwitcher(...)  # Uses LLM engine internally
rag_engine = RAGEngine()
stt_service = WhisperSTT()  # Auto-falls back to mock
tts_service = PiperTTS()     # Auto-falls back to mock
```

Test API endpoint:

```bash
cd ai-core
python3 main_api.py

# In another terminal:
curl http://localhost:8000/
# Expected: {"service": "Project Spector AI Backend", ...}
```

---

## Model Download Script

Download models easily:

```bash
cd tools

# List available models
python3 download_models.py --list

# Download specific model
python3 download_models.py llama-3-8b-instruct-gguf

# Download all (WARNING: ~5GB total)
python3 download_models.py --all
```

---

## Creating Custom LoRA Adapters

### Quick Method (Mocks for Testing)

```bash
cd tools
python3 train_lora.py --create-mocks
# Creates adapters in ai-core/models/loras/
```

### Full Training (Future)

```bash
# 1. Generate training data
python3 train_lora.py --create-dataset
# Creates: training_data/character_responses.json

# 2. Train adapter (requires GPU + training pipeline)
# TODO: Implement actual LoRA training
```

---

## Performance Modes

### Mock Mode (Current)
- **Latency**: <10ms
- **Memory**: <100MB
- **GPU**: Not required
- **Use case**: Development, testing

### CPU Inference (With Model)
- **Latency**: 500-2000ms
- **Memory**: 4-8GB
- **GPU**: Optional
- **Use case**: Production without GPU

### GPU Inference (With Model)
- **Latency**: 50-200ms
- **Memory**: 4-8GB VRAM
- **GPU**: Required (CUDA)
- **Use case**: Production, real-time interaction

---

## Troubleshooting

### "LoRA adapter not found"
- Run: `cd tools && python3 train_lora.py --create-mocks`
- Verify files exist in `ai-core/models/loras/`

### "Whisper not installed"
- This is a warning, not an error
- System uses mock transcription automatically
- Install with: `pip install openai-whisper` if needed

### "Piper not found"
- System generates silent WAV files as fallback
- Install Piper TTS separately if needed
- Check: `which piper` to verify installation

### Import errors
- Ensure you're in the `ai-core` directory
- Or add to PYTHONPATH: `export PYTHONPATH=/path/to/project-spector/ai-core:$PYTHONPATH`

---

## What Each Component Does

| Component | Real Mode | Mock Mode |
|-----------|-----------|-----------|
| **LLM Engine** | Runs llama.cpp inference | Character-aware templates |
| **LoRA Switcher** | Loads adapter weights | Loads metadata only |
| **Whisper STT** | Transcribes audio | Returns placeholder text |
| **Piper TTS** | Synthesizes speech | Generates silent WAV |
| **RAG Engine** | Text search | Text search (same) |
| **Game Master** | Event routing | Event routing (same) |

---

## Next Steps

1. **Test current setup**: All modules work in mock mode
2. **Download LLM** (optional): For real text generation 
3. **Install Whisper** (optional): For voice input
4. **Install Piper** (optional): For voice output
5. **Train LoRAs** (future): Character-specific fine-tuning

---

**Last Updated**: 2025-12-12  
**Status**: All components functional with intelligent fallbacks
