# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required (development mode).

## Endpoints

### Health Check

```http
GET /
```

**Response:**
```json
{
  "service": "Project Spector AI Backend",
  "status": "online",
  "version": "0.1.0"
}
```

---

### Process Event

```http
POST /event
```

Process a game event and return affected agents with their reactions.

**Request Body:**
```json
{
  "event_type": "property_damage",
  "action": "break_glass",
  "location": "apartment_1a",
  "noise_level": 90,
  "event_description": "Window shattered by thrown brick",
  "instigator_id": "player"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_type | string | Yes | Type: loud_noise, violence, property_damage, conversation |
| action | string | Yes | Specific action performed |
| location | string | Yes | Location identifier |
| noise_level | integer | No | 0-100 noise level |
| event_description | string | Yes | Natural language description |
| instigator_id | string | No | Who caused the event (default: "player") |

**Response:**
```json
{
  "event_id": 1,
  "timestamp": "2025-12-12T10:00:00",
  "affected_agents": ["baker_01", "landlord_01"],
  "agent_reactions": [
    {
      "agent_id": "landlord_01",
      "agent_name": "Vincent Russo",
      "lora_adapter": "vigilante_landlord.lora",
      "prompt": "You are Vincent Russo...",
      "context": {
        "recent_memories": [],
        "current_emotional_state": "neutral",
        "relationships": []
      },
      "generated_response": "Someone's going to pay for this!"
    }
  ]
}
```

---

### NPC Dialogue

```http
POST /dialogue
```

Handle player-NPC conversation.

**Request Body:**
```json
{
  "npc_id": "student_01",
  "player_message": "Did you hear that crash?",
  "context": {
    "player_reputation": 0.5,
    "time_of_day": "evening"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| npc_id | string | Yes | Agent identifier |
| player_message | string | Yes | What player said |
| context | object | No | Additional context |

**Response:**
```json
{
  "npc_id": "student_01",
  "text_response": "I'm trying to study for finals!",
  "audio_base64": "UklGRi4AAA...",
  "emotional_state": "anxious"
}
```

---

### List Agents

```http
GET /agents
```

Get all available NPCs.

**Response:**
```json
{
  "agents": [
    {
      "id": "baker_01",
      "name": "Martha Quinn",
      "archetype": "grumpy_baker",
      "lora_adapter": "grumpy_baker.lora",
      "personality_traits": ["irritable", "perfectionist"],
      "current_location": "bakery",
      "current_activity": "working_bakery",
      "emotional_state": "neutral"
    }
  ]
}
```

---

### Get Agent Details

```http
GET /agent/{agent_id}
```

Get detailed information about a specific agent.

**Path Parameters:**
- `agent_id` - Agent identifier (e.g., "baker_01")

**Response:**
```json
{
  "agent": {
    "id": "baker_01",
    "name": "Martha Quinn",
    "archetype": "grumpy_baker",
    "backstory": "Runs corner bakery for 30 years...",
    "personality_traits": ["irritable", "perfectionist"],
    "emotional_state": "neutral"
  },
  "relevant_memories": [
    {
      "timestamp": "2025-12-12T09:00:00",
      "event_description": "Teenagers loitering outside",
      "importance_score": 0.7
    }
  ],
  "relationships": [
    {
      "other_agent": "cop_01",
      "relationship_type": "acquaintance",
      "trust_level": 0.3
    }
  ]
}
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Agent not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message here"
}
```

---

## Event Types

| Type | Wake Radius | Probability | Description |
|------|-------------|-------------|-------------|
| loud_noise | 15m | 0.9 | Crashes, explosions |
| conversation | 5m | 0.7 | Speech, dialogue |
| violence | 20m | 1.0 | Combat, aggression |
| property_damage | 10m | 0.8 | Breaking objects |

---

## Usage Examples

### Python
```python
import requests

# Process event
response = requests.post('http://localhost:8000/event', json={
    'event_type': 'loud_noise',
    'action': 'player_shout',
    'location': 'street',
    'noise_level': 75,
    'event_description': 'Player yelling'
})

print(response.json())
```

### cURL
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "property_damage",
    "action": "break_glass",
    "location": "apartment_1a",
    "noise_level": 90,
    "event_description": "Window shattered"
  }'
```

### Unreal Engine (C++)
```cpp
#include "AIAPIClient.h"

UAIAPIClient* Client = NewObject<UAIAPIClient>();
Client->APIBaseURL = TEXT("http://localhost:8000");

FGameEvent Event;
Event.EventType = TEXT("loud_noise");
Event.Action = TEXT("explosion");
Event.Location = TEXT("street");
Event.NoiseLevel = 100;
Event.EventDescription = TEXT("Car exploded");

Client->SendEvent(Event);
```

---

## Rate Limits

Currently no rate limits in development mode.

Production deployment should implement:
- 100 requests/minute per IP
- 1000 events/hour per session
- Burst allowance: 20 requests/second

---

## WebSocket Support (Planned)

Future versions will support WebSocket connections for real-time streaming:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const reaction = JSON.parse(event.data);
  console.log('Agent reacted:', reaction);
};
```
