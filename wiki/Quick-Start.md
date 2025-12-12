# Quick Start Tutorial

Get Project Spector running in 5 minutes.

## Prerequisites

- Python 3.10+
- Git
- 500MB free disk space

## Step 1: Clone Repository

```bash
git clone https://github.com/Itshimcules/Spector-System.git
cd Spector-System
```

## Step 2: Set Up Environment

```bash
cd ai-core
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Expected output:
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 ...
```

## Step 3: Initialize Database

```bash
cd ../tools
python3 seed_db.py
```

Expected output:
```
Creating database at: ../ai-core/memory/vector_db/spector.db
✓ Schema created
✓ Inserted 4 agents
✓ Inserted 2 sample memories
✅ Database initialization complete!
```

## Step 4: Create Mock LoRA Adapters

```bash
python3 train_lora.py --create-mocks
```

Expected output:
```
✓ Created mock LoRA adapter: grumpy_baker.lora
✓ Created mock LoRA adapter: corrupt_cop.lora
✓ Created mock LoRA adapter: anxious_student.lora
✓ Created mock LoRA adapter: vigilante_landlord.lora
```

## Step 5: Start API Server

```bash
cd ../ai-core
python3 main_api.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Server is now running!

## Step 6: Test the System

Open a new terminal:

```bash
# Test health endpoint
curl http://localhost:8000

# Expected: {"service":"Project Spector AI Backend","status":"online"}
```

Test event processing:

```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "loud_noise",
    "action": "crash",
    "location": "street",
    "noise_level": 85,
    "event_description": "Car accident"
  }' | python3 -m json.tool
```

Expected: JSON with affected agents

## Step 7: Test Individual Components

```bash
cd ai-core

# Test Game Master
python3 orchestration/game_master.py

# Test LLM Engine
python3 models/llm_engine.py

# Test Voice Services
python3 voice/stt_whisper.py
```

All should run without errors.

## Understanding the Output

When you send an event, you'll see:

```json
{
  "event_id": 1,
  "affected_agents": ["baker_01", "cop_01", "student_01"],
  "agent_reactions": [
    {
      "agent_id": "baker_01",
      "agent_name": "Martha Quinn",
      "generated_response": "I don't have time for this nonsense!"
    }
  ]
}
```

This shows:
- Which NPCs heard the event
- Their character-specific reactions
- Context for their response

## What's Happening?

1. **Event Sent** → API receives game event
2. **Game Master** → Calculates which NPCs react
3. **LoRA Switcher** → Loads character personalities
4. **LLM Engine** → Generates responses (mock mode)
5. **Response** → Returns to game client

## Mock Mode vs Real Mode

**You're currently in Mock Mode:**
- No model downloads needed
- Instant responses
- Character-aware but template-based

**To enable Real Mode:**
```bash
# Download LLM (4GB)
cd tools
python3 download_models.py llama-3-8b-instruct-gguf

# Install llama-cpp
pip install llama-cpp-python
```

## Exploring the System

### View Database

```bash
cd ai-core/memory/vector_db
sqlite3 spector.db

# SQL commands:
.tables                    # Show all tables
SELECT * FROM agents;      # View NPCs
SELECT * FROM episodic_memory;  # View memories
.quit
```

### View Character Metadata

```bash
cd ai-core/models/loras
cat grumpy_baker.json
```

### Modify Characters

```bash
cd ai-core/config
nano agents.yaml           # Edit character definitions
```

## Common Issues

**Port 8000 in use:**
```bash
# Use different port
python3 main_api.py --port 8001
```

**Database not found:**
```bash
# Re-initialize
cd tools
python3 seed_db.py
```

**Import errors:**
```bash
# Make sure you're in ai-core directory
cd ai-core
python3 main_api.py
```

## Next Steps

1. **Read Architecture** - Understand how it works
   - [Architecture Overview](Architecture)

2. **Create Characters** - Add your own NPCs
   - [Creating Characters](Creating-Characters)

3. **Integrate with Unreal** - Build 3D environment
   - [Unreal Integration](Unreal-Integration)

4. **Download Models** - Enable real AI
   - [Model Integration](Model-Integration)

## Quick Reference

```bash
# Start server
cd ai-core && python3 main_api.py

# Test endpoint
curl http://localhost:8000

# View logs
# (shown in terminal where server is running)

# Stop server
# Press Ctrl+C in server terminal

# Recreate database
cd tools && python3 seed_db.py

# Create new characters
cd tools && python3 train_lora.py --create-mocks
```

## Success!

You now have:
- Working API server
- 4 unique NPCs with personalities
- Database with memory storage
- Character-aware response system

Ready to build your simulation!
