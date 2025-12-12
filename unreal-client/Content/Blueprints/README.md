# Unreal Engine Blueprints

## Core Blueprints

### BP_NPC_Base.uasset
Base blueprint for all NPC characters. Handles:
- HTTP requests to AI backend (localhost:8000)
- Audio playback for TTS responses
- Animation state based on emotional state
- Proximity detection for LoRA pre-loading

**Key Functions:**
- `SendEventToAI(EventData)` - Notify backend of NPC observations
- `RequestDialogue(PlayerMessage)` - Get NPC response to player
- `PlayVoiceResponse(AudioData)` - Play TTS audio
- `UpdateEmotionalState(State)` - Change animation/expression

### BP_GameMaster.uasset
Global event listener blueprint. Handles:
- Broadcasting physics events (breaking glass, explosions)
- Player action tracking
- Coordination with AI Game Master

**Key Functions:**
- `BroadcastEvent(EventType, Location, Metadata)`
- `ProcessAIResponse(AgentReactions)`
- `SpawnNPCReaction(AgentID, Action)`

## Implementation Notes

These blueprints need to be created in Unreal Editor. This file serves as documentation
for the expected functionality.

To implement:
1. Create blueprints in Content/Blueprints/
2. Add HTTP request nodes (VaRest plugin recommended)
3. Connect to C++ classes in Source/SpectorSim/ for low-latency calls
