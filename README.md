# Project Spector: High-Density "One City Block" Simulation

> **"A simulation where the player cannot travel for miles, but can enter every room, open every drawer, speak to every resident, and disrupt every routine."**

## 📖 Abstract

**Project Spector** is an open-source framework designed to realize Warren Spector's theoretical "One City Block" RPG concept. Historically, this vision was impossible due to the "Authoring Bottleneck"—the inability to manually script deep behaviors for hundreds of characters.

This project solves that bottleneck by replacing deterministic scripting with **Local Generative AI Architecture**. By orchestrating multi-agent systems, memory storage, and dynamic personality loading, we create a framework for living worlds that emerge from independent agents.

## 📊 Project Status

**Current Phase**: Prototype Framework

This repository contains the core architecture and orchestration layer for Project Spector. The foundation is complete and functional:

- ✅ FastAPI backend with event processing
- ✅ Game Master event routing system  
- ✅ LoRA adapter management (awaiting model files)
- ✅ Memory storage with text search
- ✅ C++ client for Unreal Engine integration
- ⚠️ Voice services (stub implementations)
- ⚠️ AI model integration (in progress)
- ⚠️ Unreal Engine environment (not included)

**What works now**: Event orchestration, agent selection, prompt generation, database operations.  
**What's needed**: LLM model files, LoRA adapters, Unreal Engine implementation.

## 🏗️ Architecture

The system is composed of three distinct "Pillars" that bridge the gap between traditional game loops and Generative AI.

### 1. The Game Master (Causal Engine)

* **Role:** The "Concordia" Pattern.
* **Function:** Instead of hard-coded triggers, the GM agent "listens" to the simulation. When a player performs an action (e.g., throwing a brick), the GM calculates the "semantic radius" of the event and wakes up relevant agents.
* **Implementation:** Semantic Kernel (C#) acting as the event broadcaster.

### 2. The Hive Mind (LoRA Switching)

* **Role:** Solving the "Cast of Hundreds" problem.
* **Function:** We cannot run 200 LLMs simultaneously. Instead, we run **one** base model (Llama-3-8B Quantized) and dynamically hot-swap **Low-Rank Adapters (LoRAs)** based on who is speaking.
* **Implementation:** `Adapter_GrumpyBaker`, `Adapter_CorruptCop`, etc., loaded into memory on-the-fly.

### 3. The Infinite Drawer (Vector RAG)

*   **Role:** Persistent Object History.
*   **Function:** Every object and NPC has a vector embedding. If an NPC mentions a locket lost 3 years ago, that data is retrieved from the Vector DB, ensuring narrative consistency (Chekhov's Gun).
*   **Implementation:** `SQLite-vec` for local, low-latency vector search.

## 🛠️ Tech Stack

| Component | Technology | Status |
|:---|:---|:---|
| **Backend** | FastAPI + Python 3.10+ | ✅ Implemented |
| **Database** | SQLite with text search | ✅ Implemented |
| **Engine** | Unreal Engine 5 (C++ client) | ⚠️ Interface only |
| **Inference** | Llama-3-8B (planned) | ⏳ Not integrated |
| **Personalities** | LoRA Adapters | ⏳ Awaiting files |
| **Voice STT** | Whisper | ⏳ Stub only |
| **Voice TTS** | Piper | ⏳ Stub only |

## 🚀 Getting Started

> **Note**: This is an early-stage prototype. The framework is functional but AI model integration is in progress.

### Prerequisites

* **Python**: 3.10+ recommended
* **OS**: Linux, Windows (WSL2), or macOS
* **Optional**: NVIDIA GPU for future model integration

### Installation

#### 1. Set up the AI Core

```bash
cd ai-core
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Initialize the Database

```bash
cd tools
python3 seed_db.py
```

#### 3. Start the API Server

```bash
cd ai-core
python3 main_api.py
```

Server will start on: `http://localhost:8000`

#### 4. Test the System

```bash
# Test Game Master
python3 orchestration/game_master.py

# Test LoRA switcher
python3 orchestration/lora_switcher.py
```

## 🧠 Usage Example: The "Broken Window" Scenario

1. **Player Action:** In UE5, the player throws a physics object (Brick) at a window.
2. **Event Log:** UE5 sends a JSON payload to `localhost:8000/event`: `{ "action": "break_glass", "location": "Apt 1A", "noise_level": 90 }`.
3. **GM Processing:** The Python Game Master queries the Vector DB for agents within "hearing range."
4. **Reaction:**
    * *Agent A (Neighbor):* Loaded with `LoRA_Anxious`. Receives prompt: "Loud crash next door." Output: "Hides under bed."
    * *Agent B (Landlord):* Loaded with `LoRA_Vigilante`. Output: "Grabs bat, moves to Apt 1A."
5. **Result:** UE5 receives instructions to spawn the Landlord NPC moving toward the player.

## 🤝 Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for details on how to train new LoRA adapters or optimize the RAG pipeline.

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details.
