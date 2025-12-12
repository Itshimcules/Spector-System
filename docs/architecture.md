# Architecture Overview

## System Flow Diagram

```
┌─────────────────┐
│  Unreal Engine  │
│   Game Client   │
└────────┬────────┘
         │ HTTP/WebSocket
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
```

## Component Responsibilities

### Game Client (Unreal Engine 5)
- Renders the 3D environment
- Handles player input and physics
- Sends events to AI backend
- Receives and executes AI-generated instructions

### AI Backend (Python)
- **Game Master**: Event orchestration and agent coordination
- **LoRA Switcher**: Dynamic personality loading
- **RAG Engine**: Vector memory retrieval
- **Voice Service**: STT/TTS processing

## Data Flow Example

1. Player breaks window in UE5
2. UE5 sends event: `{action: "break_glass", location: "Apt1A", noise: 90}`
3. Game Master calculates semantic radius
4. RAG retrieves nearby NPCs from vector DB
5. LoRA Switcher loads relevant personality adapters
6. LLM generates NPC reactions
7. Responses sent back to UE5
8. NPCs execute behaviors in game world

## Latency Optimization

- **Pre-fetching**: Load LoRA adapters when player approaches NPCs
- **Caching**: Keep frequently used embeddings in memory
- **Async Processing**: Non-blocking API calls
- **Local Inference**: No cloud latency
