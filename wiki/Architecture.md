# Architecture Overview

## System Design

Project Spector uses a three-pillar architecture that bridges traditional game engines with generative AI:

```
┌─────────────────┐
│  Unreal Engine  │
│   Game Client   │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────────┐
│        FastAPI Backend              │
│         (main_api.py)               │
└─────────┬───────────────────────────┘
          │
    ┌─────┴─────┬──────────┬─────────┐
    ▼           ▼          ▼         ▼
┌────────┐ ┌─────────┐ ┌──────┐ ┌────────┐
│Game    │ │ LoRA    │ │ RAG  │ │Voice   │
│Master  │ │Switcher │ │Engine│ │Service │
└────────┘ └─────────┘ └──────┘ └────────┘
    │           │          │         │
    └───────────┴──────────┴─────────┘
                  │
            ┌─────▼──────┐
            │   SQLite   │
            │  Database  │
            └────────────┘
```

## Three Pillars

### 1. Game Master (Causal Engine)

**Purpose:** Event orchestration and agent coordination

**How it works:**
- Listens to game events from Unreal Engine
- Calculates "semantic radius" for each event
- Determines which NPCs should react
- Generates contextual prompts

**Key Features:**
- Event type mapping (noise, violence, conversation)
- Wake probability system
- Distance calculations
- AgentHistory logging

**File:** `ai-core/orchestration/game_master.py`

### 2. LoRA Switcher (Hive Mind)

**Purpose:** Dynamic personality loading

**Problem Solved:** Can't run 200 LLMs simultaneously

**Solution:** One base model + hot-swappable LoRA adapters

**How it works:**
- LRU cache holds 3 adapters in memory
- Loads/unloads adapters as NPCs speak
- Each adapter = unique personality (~50MB)
- Character metadata enhances prompts

**Key Features:**
- Cache hit/miss tracking
- Pre-loading for nearby NPCs
- Character trait integration
- Mock mode for development

**File:** `ai-core/orchestration/lora_switcher.py`

### 3. RAG Engine (Infinite Drawer)

**Purpose:** Persistent memory and narrative consistency

**Chekhov's Gun Principle:** If an NPC mentions a locket, it must exist

**How it works:**
- Stores every event in SQLite
- Text-based search for memory retrieval
- Tracks relationships between NPCs
- World object persistence

**Key Features:**
- Episodic memory storage
- Importance scoring
- Relationship dynamics
- Object history tracking

**File:** `ai-core/orchestration/rag_engine.py`

## Data Flow

### Example: Breaking a Window

1. **Player Action**
   - Player throws brick at window in Unreal Engine
   - Physics engine triggers "break_glass" event

2. **Event Sent to API**
   ```json
   POST /event
   {
     "event_type": "property_damage",
     "action": "break_glass",
     "location": "apartment_1a",
     "noise_level": 90,
     "event_description": "Window shattered"
   }
   ```

3. **Game Master Processing**
   - Calculates semantic radius: 10 meters
   - Queries database for NPCs within range
   - Finds 4 agents: baker, cop, student, landlord
   - Applies wake probability (0.8 for property damage)

4. **Agent Reactions**
   - For each agent:
     - Load LoRA adapter (e.g., "grumpy_baker.lora")
     - Retrieve relevant memories from RAG
     - Generate character-specific prompt
     - Get LLM response

5. **Response Example**
   ```json
   {
     "agent_id": "landlord_01",
     "agent_name": "Vincent Russo",
     "response": "Someone's going to pay for this damage!",
     "action": "move_to_location_1a",
     "emotional_state": "angry"
   }
   ```

6. **Unreal Engine Execution**
   - Receives agent reactions
   - Spawns/activates NPCs
   - Plays animations
   - Triggers dialogue

## API Endpoints

### POST /event
Process game event and return agent reactions

**Request:**
```json
{
  "event_type": "loud_noise",
  "action": "player_shout",
  "location": "street",
  "noise_level": 75,
  "event_description": "Player yelling"
}
```

**Response:**
```json
{
  "affected_agents": ["cop_01", "baker_01"],
  "agent_reactions": [...]
}
```

### POST /dialogue
NPC conversation with player

**Request:**
```json
{
  "npc_id": "student_01",
  "player_message": "Did you hear that crash?"
}
```

**Response:**
```json
{
  "text_response": "I'm trying to study!",
  "audio_base64": "...",
  "emotional_state": "anxious"
}
```

### GET /agents
List all available NPCs

### GET /agent/{id}
Get agent details and context

## Database Schema

```sql
-- Core tables
agents              -- NPC definitions
episodic_memory     -- Event history
world_objects       -- Persistent items
relationships       -- NPC-to-NPC dynamics  
event_log           -- Game Master history
```

See [Database Schema](Database-Schema) for details.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Game Engine | Unreal Engine 5 | 3D rendering, physics |
| API Server | FastAPI | REST endpoints |
| Orchestration | Python 3.10+ | AI coordination |
| LLM Inference | llama-cpp-python | Text generation |
| Voice STT | OpenAI Whisper | Speech recognition |
| Voice TTS | Piper | Speech synthesis |
| Database | SQLite | Persistent storage |
| Character AI | LoRA adapters | Personalities |

## Design Principles

1. **Graceful Degradation**
   - System works without models (mock mode)
   - Automatic fallbacks for missing components

2. **Event-Driven**
   - No polling
   - Reactive to player actions
   - Efficient resource usage

3. **Modular**
   - Each pillar independent
   - Easy to swap implementations
   - Clear interfaces

4. **Emergent Behavior**
   - No scripted sequences
   - NPCs react based on personality + context
   - Unpredictable but believable outcomes

## Performance Targets

- **Event Processing:** <50ms
- **LLM Inference:** <500ms (CPU), <100ms (GPU)
- **Voice Round-trip:** <1000ms
- **Memory Retrieval:** <10ms
- **Frame Rate:** 60 FPS in Unreal

## Next Steps

- [Game Master System](Game-Master)
- [LoRA Adapter System](LoRA-Adapters)
- [Memory System](Memory-System)
