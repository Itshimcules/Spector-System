# Project Spector

### A local-first generative AI framework for deep NPC simulation — Warren Spector's "One City Block," finally buildable.

[![tests](https://github.com/Itshimcules/Spector-System/actions/workflows/tests.yml/badge.svg)](https://github.com/Itshimcules/Spector-System/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](ai-core/requirements.txt)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-prototype-orange.svg)](#project-status)

> **"A simulation where the player cannot travel for miles, but can enter every room, open every drawer, speak to every resident, and disrupt every routine."**

**[Read the Whitepaper](docs/WHITEPAPER.md)** — the full problem statement, architecture, and engineering analysis.

---

## The Pitch

Deep, reactive NPCs have never been a creative problem — they are an **economic** one. Hand-scripting dialogue trees and behavior branches for hundreds of characters is an authoring cost no studio can pay, so "living worlds" ship with three bark lines per resident.

Project Spector replaces scripting with **generation**, under constraints game developers actually have:

- **One brain, many masks.** A single quantized local LLM (Llama-3-8B class) portrays the entire cast by hot-swapping lightweight **LoRA personality adapters** — a new character costs a fine-tune, not a writing team.
- **Events, not polling.** A **Game Master** orchestrator computes each event's *semantic radius* and wakes only the characters who would plausibly notice. Idle NPCs cost nothing.
- **Memory makes characters.** Every agent and object has persistent, queryable history — episodic memory, relationships, object significance — so reactions stay consistent with *your player's* world.
- **Local-first.** No cloud endpoint, no per-token bill, no online dependency in a shipped game. Runs on a consumer GPU; develops on a laptop with **zero model downloads** thanks to mock fallbacks.
- **Engine-agnostic.** The AI core is a four-endpoint JSON/HTTP service. UE5 (C++ client included) is the reference integration; Unity or Godot is an afternoon of transport code.

## Why Game Developers Should Care

| You have | Spector gives you |
|:---|:---|
| An engine with physics, animation, navigation | A drop-in **decision and dialogue layer** — your systems stay authoritative for execution |
| A world full of placeholder NPCs | Characters with schedules, personalities, memory, and improvised reactions to unscripted player behavior |
| A latency budget | Async ambient reactions (~human reaction time), GPU dialogue at 50–200 ms, adapter prefetch on player proximity |
| No ML infrastructure | An embedded SQLite memory store and llama.cpp inference — no servers, no ops |

Try the full event pipeline in five minutes, no GPU, no model files: see [Getting Started](#getting-started).

## Project Status

**Current phase: prototype framework.** The orchestration foundation is complete, tested, and CI-covered; real model integration is the active milestone. We are explicit about this split — see [Section 8 of the whitepaper](docs/WHITEPAPER.md#8-current-status-and-limitations) for the candid version.

- [x] FastAPI backend with event processing
- [x] Game Master event routing (semantic radius, wake probabilities)
- [x] LoRA adapter management (LRU cache + proximity prefetch)
- [x] Persistent memory: agents, episodic memory, world objects, relationships, event log
- [x] C++ client for Unreal Engine integration
- [x] Voice services (Whisper STT + Piper TTS with graceful mock fallback)
- [x] Pytest suite covering orchestration, memory, and voice layers
- [ ] AI model integration (in progress — LLM model files needed)
- [ ] Trained LoRA adapters (scaffolding and dataset format exist)
- [ ] Unreal Engine playable environment (interface only)

## Architecture

Three pillars bridge the gap between traditional game loops and generative AI. Full detail in the [whitepaper](docs/WHITEPAPER.md) and [architecture overview](docs/architecture.md).

```
 Unreal Engine 5  ──JSON/HTTP──►  AI Core (FastAPI)
 (render, physics,                ├─ Game Master      event orchestration
  input, animation)               ├─ LoRA Switcher    one LLM, many personalities
                  ◄──reactions──  ├─ RAG Engine       persistent world memory
                                  └─ Voice Service    Whisper STT / Piper TTS
```

### 1. The Game Master (Causal Engine)
Instead of hard-coded triggers, the GM "listens" to the simulation. When the player acts, it computes the event's **semantic radius** and wakes only relevant agents, each with a wake probability tuned per event class (violence carries farther than conversation).

### 2. The Hive Mind (LoRA Switching)
You cannot run 200 LLMs; you don't need to. One quantized base model hot-swaps **Low-Rank Adapters** — `grumpy_baker`, `corrupt_cop`, `anxious_student`, `vigilante_landlord` — managed by an LRU cache with proximity-based prefetch.

### 3. The Infinite Drawer (Persistent Memory)
Every NPC and object accrues history in an embedded SQLite store: importance-scored episodic memory, pairwise trust relationships, and object significance tracking. A locket mentioned once can resurface, correctly contextualized, hours later — Chekhov's Gun as a database feature.

## Usage Example: The "Broken Window" Scenario

1. **Player action:** In UE5, the player throws a brick through a window.
2. **Event report:** UE5 POSTs to `localhost:8000/event`:
   `{ "event_type": "property_damage", "action": "break_glass", "location": "apartment_1a", "noise_level": 90, "event_description": "A window has been shattered by a thrown brick." }`
3. **Orchestration:** The Game Master resolves radius 10.0 / wake probability 0.8 and selects agents in range.
4. **Reactions:**
   - *Emily Chen* (`anxious_student`, home in 1A): hides under the bed, too scared to call the police.
   - *Vincent Russo* (`vigilante_landlord`, ex-military, his building): grabs a bat and heads for Apartment 1A.
5. **Result:** UE5 receives structured reactions and drives navigation and dialogue. Both agents write the event to memory — tomorrow, the baker will have heard about it.

No author scripted any branch of this.

## Tech Stack

| Component | Technology | Status |
|:---|:---|:---|
| **Backend** | FastAPI + Python 3.10+ | Implemented |
| **Memory** | SQLite (WAL) with text search; `sqlite-vec` planned | Implemented |
| **Engine client** | Unreal Engine 5 (C++ `AIAPIClient` + Blueprint interface) | Interface only |
| **Inference** | llama.cpp / Llama-3-8B quantized (planned) | Mock mode |
| **Personalities** | LoRA adapters + JSON metadata | Awaiting trained weights |
| **Voice STT** | Whisper | Implemented (mock fallback) |
| **Voice TTS** | Piper | Implemented (mock fallback) |

## Getting Started

> Everything below works with **no model downloads and no GPU** — all AI components fall back to deterministic mocks, so you can evaluate the full pipeline immediately.

### Prerequisites

- **Python** 3.10+
- **OS:** Linux, Windows (WSL2), or macOS
- **Optional:** NVIDIA GPU for real model inference later

### 1. Set up the AI Core

```bash
cd ai-core
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` is pure-Python and needs no compiler or model files — it is
all you need for mock mode. Real models (local LLM, Whisper) are an optional,
heavier install: `pip install -r requirements-ml.txt`.

### 2. Initialize the Database

```bash
cd tools
python3 seed_db.py
```

### 3. Start the API Server

```bash
cd ai-core
python3 main_api.py
# Server: http://localhost:8000  (interactive docs at /docs)
```

> No `config/settings.json`? The server automatically falls back to the
> committed `config/settings.example.json`, so it runs out of the box. Copy the
> example to `settings.json` only when you want to customize (it's git-ignored).

### 4. Throw a brick

```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"event_type":"property_damage","action":"break_glass","location":"apartment_1a","noise_level":90,"event_description":"A window has been shattered by a thrown brick."}'
```

All four agents react in character — `grumpy_baker`, `corrupt_cop`,
`anxious_student`, and `vigilante_landlord` adapters are served in metadata-only
mock mode, so the full pipeline returns `200` with no model files present.

### 5. Run the Test Suite

```bash
cd ai-core
pip install -r requirements.txt pytest   # core deps + pytest
pytest tests/ -v
```

When you're ready for real inference, see [AI_INTEGRATION.md](AI_INTEGRATION.md) for model setup (`pip install -r requirements-ml.txt` plus a model download).

## Documentation

| Document | What's in it |
|:---|:---|
| **[Whitepaper](docs/WHITEPAPER.md)** | Problem statement, full architecture, latency engineering, honest limitations, references |
| [Architecture Overview](docs/architecture.md) | System flow and component responsibilities |
| [Concept Paper](docs/concept_paper.md) | The "One City Block" theoretical foundation |
| [AI Integration Guide](AI_INTEGRATION.md) | Adding real models: LLM, Whisper, Piper, LoRA training |
| [Setup Guide](SETUP.md) | Detailed installation and configuration |
| [Roadmap](ROADMAP.md) | Phase-by-phase milestones through public release |
| [Status](STATUS.md) | Component-level implementation status |
| [Wiki](wiki/Home.md) | Quick start, API reference, character creation, troubleshooting |

## Contributing

We welcome contributions — most valuable right now: LoRA training expertise, Unreal Engine developers, character writers, and performance work. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE). Build games with it.
