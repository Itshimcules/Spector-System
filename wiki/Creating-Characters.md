# Creating Characters

Learn how to create unique NPCs with distinct personalities using LoRA adapters.

## Character Design Process

### 1. Define Character Concept

Start with core traits and backstory:

```yaml
name: "Sarah Mitchell"
archetype: "paranoid_detective"
age: 42
occupation: "Private Investigator"
```

**Key Questions:**
- What drives this character?
- How do they react under stress?
- What's their relationship to others?
- What's their daily routine?

### 2. Create Personality Profile

Define 3-5 core traits that influence behavior:

```yaml
personality_traits:
  - suspicious
  - detail_oriented
  - insomniac
  - protective
  - cynical
```

**Trait Guidelines:**
- Be specific (not "nice" but "overly helpful")
- Mix positive and negative
- Ensure traits can conflict (creates depth)
- Consider how traits manifest in speech

### 3. Write Backstory

Keep it concise but meaningful:

```yaml
backstory: >
  Former police detective turned PI after uncovering corruption.
  Lives above her office, rarely sleeps. Trusts no one but
  always helps victims. Solving cases is her only purpose.
```

**Backstory Tips:**
- 2-3 sentences maximum
- Include motivation
- Hint at relationships
- Explain current situation

### 4. Define Schedule

Create realistic daily routine:

```yaml
schedule:
  - time: "00:00-06:00"
    activity: "investigating"
    location: "office"
  - time: "06:00-08:00"
    activity: "coffee_and_files"
    location: "office"
  - time: "08:00-18:00"
    activity: "fieldwork"
    location: "city_streets"
  - time: "18:00-24:00"
    activity: "investigating"
    location: "office"
```

### 5. Add to agents.yaml

```bash
cd ai-core/config
nano agents.yaml
```

Add your character:

```yaml
- id: "detective_01"
  name: "Sarah Mitchell"
  archetype: "paranoid_detective"
  lora_adapter: "paranoid_detective.lora"
  personality_traits:
    - suspicious
    - detail_oriented
    - insomniac
  backstory: "Former police detective..."
  voice_id: "female_middle_aged_02"
  current_location: "office"
  current_activity: "investigating"
  emotional_state: "alert"
  schedule:
    - time: "00:00-06:00"
      activity: "investigating"
      location: "office"
```

## Creating Training Data

### Manual Approach

Create training samples in `tools/training_data/`:

```json
{
  "character": "paranoid_detective",
  "samples": [
    {
      "situation": "Hears suspicious noise",
      "response": "Nothing's ever just a coincidence. I'm checking it out."
    },
    {
      "situation": "Stranger asks for help",
      "response": "What's your angle? Nobody helps for free."
    },
    {
      "situation": "Finds evidence",
      "response": "Finally. This connects to the Miller case from '09."
    }
  ]
}
```

**Quality Guidelines:**
- 20+ samples minimum
- Vary situations (stress, calm, angry, sad)
- Show personality through word choice
- Keep responses 1-2 sentences
- Use character's vocabulary

### Automated Generation

Use the training script:

```python
# In tools/train_lora.py, add your character:

CHARACTER_TEMPLATES = {
    'paranoid_detective': {
        'base_traits': ['suspicious', 'detail_oriented', 'cynical'],
        'speech_patterns': [
            'questions motives',
            'references past cases',
            'uses detective jargon'
        ],
        'sample_responses': [
            "I've seen this pattern before. It never ends well.",
            "Trust is earned, and you haven't earned it yet.",
            "The evidence doesn't lie. People do."
        ]
    }
}
```

Run generation:

```bash
cd tools
python3 train_lora.py --character paranoid_detective --create-dataset
```

## Creating LoRA Adapter

### Mock Adapter (For Testing)

```bash
cd tools
python3 train_lora.py --character paranoid_detective --create-mocks
```

Creates:
- `ai-core/models/loras/paranoid_detective.lora`
- `ai-core/models/loras/paranoid_detective.json`

### Real LoRA Training (Advanced)

**Requirements:**
- NVIDIA GPU with 8GB+ VRAM
- Training dataset (100+ samples)
- Base model downloaded

**Process:**
```bash
# 1. Prepare dataset
python3 train_lora.py --create-dataset

# 2. Train adapter (requires PEFT)
# TODO: Implement full training pipeline
```

**Training Parameters:**
```yaml
rank: 8              # LoRA rank
alpha: 16            # Scaling factor  
target_modules:      # Which layers to adapt
  - q_proj
  - v_proj
epochs: 3
batch_size: 4
learning_rate: 3e-4
```

## Testing Your Character

### 1. Test in Python

```python
from orchestration.lora_switcher import LoRASwitcher

switcher = LoRASwitcher(
    base_model_path="models/base/model.gguf",
    lora_directory="models/loras"
)

response = switcher.generate_response(
    "paranoid_detective.lora",
    "Someone broke into your office. How do you react?"
)

print(response)
```

### 2. Test via API

```bash
# Start server
cd ai-core
python3 main_api.py &

# Test dialogue
curl -X POST http://localhost:8000/dialogue \
  -H "Content-Type: application/json" \
  -d '{
    "npc_id": "detective_01",
    "player_message": "I need your help"
  }'
```

### 3. Check Character Consistency

Ask 10 different questions, verify:
- Personality traits show through
- Speech patterns consistent
- Reactions fit backstory
- No out-of-character responses

## Character Relationships

Define how characters interact:

```sql
-- In database
INSERT INTO relationships (agent_id_1, agent_id_2, relationship_type, trust_level)
VALUES 
  ('detective_01', 'cop_01', 'rivalry', -0.3),
  ('detective_01', 'baker_01', 'regular_customer', 0.6);
```

**Relationship Types:**
- friend, enemy, acquaintance
- romantic, family
- professional, rivalry
- stranger

**Trust Levels:**
- -1.0 = Complete distrust
- 0.0 = Neutral
- 1.0 = Complete trust

## Voice Selection

Match voice to character:

```yaml
voice_id: "female_middle_aged_02"
```

**Available Voices:**
- female_young_01 - 20s, cheerful
- female_middle_aged_01 - 40s, professional
- male_older_01 - 60s, gruff
- male_young_01 - 20s, energetic

(Requires Piper TTS installation)

## Common Pitfalls

**Too Generic**
- Bad: "angry person"
- Good: "rage-filled ex-boxer with PTSD"

**Inconsistent Traits**
- Don't make shy character extroverted
- Don't give coward brave responses

**Over-complicated**
- Keep to 3-5 core traits
- Simple backstory (2-3 sentences)

**No Flaws**
- Perfect characters are boring
- Add weaknesses, fears, quirks

## Example Characters

### Minimalist Approach

```yaml
id: "janitor_01"
name: "Frank"
traits: [quiet, observant, helpful]
backstory: "Building janitor for 20 years. Sees everything, says nothing."
```

### Detailed Approach

```yaml
id: "hacker_01"
name: "Alex Chen"
archetype: "paranoid_hacker"
traits:
  - paranoid
  - brilliant
  - nocturnal
  - agoraphobic
  - compulsive
backstory: >
  Former NSA contractor turned whistleblower. Lives entirely
  online, hasn't left apartment in 3 years. Brilliant but
  unstable. Trusts encryption more than people.
voice_id: "neutral_synthetic_01"
schedule:
  - time: "00:00-12:00"
    activity: "sleeping"
    location: "apartment_3b"
  - time: "12:00-24:00"
    activity: "hacking"
    location: "apartment_3b"
```

## Next Steps

- [Training LoRAs](Training-LoRAs) - Full training guide
- [Database Schema](Database-Schema) - How character data is stored
- [API Reference](API-Reference) - Testing characters via API
