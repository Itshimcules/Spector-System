# Installation Guide

## System Requirements

### Minimum
- **OS:** Linux, Windows 10+, or macOS
- **Python:** 3.10 or higher
- **RAM:** 4GB
- **Storage:** 500MB (without models)

### Recommended
- **OS:** Ubuntu 22.04 or Windows 11
- **Python:** 3.11+
- **RAM:** 16GB
- **GPU:** NVIDIA GPU with 8GB+ VRAM (for real LLM inference)
- **Storage:** 10GB (with models)

## Quick Install (Mock Mode)

This gets you running immediately without downloading models:

```bash
# Clone repository
git clone https://github.com/Itshimcules/Spector-System.git
cd Spector-System

# Set up Python environment
cd ai-core
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
cd ../tools
python3 seed_db.py

# Start API server
cd ../ai-core
python3 main_api.py
```

Server runs at `http://localhost:8000`

## Full Install (With Models)

### 1. Install Core Dependencies

```bash
# Same as Quick Install above
cd ai-core
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install llama-cpp-python

```bash
# CPU only
pip install llama-cpp-python

# With CUDA support (NVIDIA GPU)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

### 3. Download Models

```bash
cd tools

# Download LLM (4GB)
python3 download_models.py llama-3-8b-instruct-gguf

# Whisper auto-downloads on first use
pip install openai-whisper
```

### 4. Install Piper TTS (Optional)

**Ubuntu/Debian:**
```bash
sudo apt install piper-tts
```

**From Source:**
```bash
# See: https://github.com/rhasspy/piper
```

### 5. Create LoRA Adapters

```bash
cd tools
python3 train_lora.py --create-mocks
```

## Verify Installation

```bash
cd ai-core

# Test LLM engine
python3 models/llm_engine.py

# Test Game Master
python3 orchestration/game_master.py

# Test API
python3 main_api.py &
curl http://localhost:8000
```

## Troubleshooting

### "llama-cpp-python not found"
- You're in mock mode (expected)
- Install with: `pip install llama-cpp-python`

### "Database not found"
- Run: `cd tools && python3 seed_db.py`

### "Port 8000 already in use"
- Change port: `python3 main_api.py --port 8001`
- Or kill existing: `lsof -ti:8000 | xargs kill`

### CUDA errors
- Verify NVIDIA drivers: `nvidia-smi`
- Reinstall with CUDA: `CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall`

## Next Steps

- [Quick Start Tutorial](Quick-Start)
- [Architecture Overview](Architecture)
- [API Reference](API-Reference)
