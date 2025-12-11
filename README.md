# Spector-System
Realizing Warren Spector's "One City Block" concept via Local AI. A UE5 framework utilizing multi-agent orchestration, dynamic LoRA switching, and Vector RAG to create high-density, unscripted simulation where every NPC and object has infinite depth.

> "A simulation where the player cannot travel for miles, but can enter every room, open every drawer, speak to every resident, and disrupt every routine."
> 
Abstract
Project Spector is an open-source framework designed to realize Warren Spector’s theoretical "One City Block" RPG concept. Historically, this vision was impossible due to the "Authoring Bottleneck"—the inability to manually script deep behaviors for hundreds of characters.
This project solves that bottleneck by replacing deterministic scripting with Local Generative AI Architecture. By orchestrating multi-agent systems, vector databases, and dynamic LoRA switching, we create a living world that emerges naturally from the collision of independent agents.
Architecture
The system is composed of three distinct "Pillars" that bridge the gap between traditional game loops and Generative AI.
1. The Game Master (Causal Engine)
 * Role: The "Concordia" Pattern.
 * Function: Instead of hard-coded triggers, the GM agent "listens" to the simulation. When a player performs an action (e.g., throwing a brick), the GM calculates the "semantic radius" of the event and wakes up relevant agents.
 * Implementation: Semantic Kernel (C#) acting as the event broadcaster.
2. The Hive Mind (LoRA Switching)
 * Role: Solving the "Cast of Hundreds" problem.
 * Function: We cannot run 200 LLMs simultaneously. Instead, we run one base model (Llama-3-8B Quantized) and dynamically hot-swap Low-Rank Adapters (LoRAs) based on who is speaking.
 * Implementation: Adapter_GrumpyBaker, Adapter_CorruptCop, etc., loaded into memory on-the-fly.
3. The Infinite Drawer (Vector RAG)
 * Role: Persistent Object History.
 * Function: Every object and NPC has a vector embedding. If an NPC mentions a locket lost 3 years ago, that data is retrieved from the Vector DB, ensuring narrative consistency (Chekhov’s Gun).
 * Implementation: SQLite-vec for local, low-latency vector search.

Tech Stack
| Component | Technology | Role |
|---|---|---|
| Engine | Unreal Engine 5 | Nanite/Lumen for high-fidelity rendering. |
| Inference | Azure Foundry Local | Running Llama-3-8B (Quantized) locally. |
| Personalities | LoRA Adapters | 50MB "personality cartridges" swapped at runtime. |
| Memory | SQLite-vec | Local Vector Database for episodic memory. |
| Voice | Whisper & Piper | STT and TTS for <500ms conversation latency. |
| Orchestration | Semantic Kernel | Managing the agentic loop. |

Getting Started
Prerequisites

 * GPU: NVIDIA RTX 3060 (12GB VRAM) or higher recommended.

 * OS: Windows 10/11 or Ubuntu 22.04 (WSL2 supported).
 
* Software: Unreal Engine 5.3+, Docker, Python 3.10+.

Installation

1. Set up the AI Core
cd ai-core
pip install -r requirements.txt
# Download the base Llama-3 model
python tools/download_model.py --model llama-3-8b-quantized
# Initialize the Vector Database
python tools/seed_db.py
# Start the API Server
python main_api.py --port 8000

2. Configure the Game Client
 * Open unreal-client/ProjectSpector.uproject.
 * Navigate to Content/Blueprints/BP_GameInstance.
 * Set the AI_API_URL variable to http://localhost:8000.
 Usage Example: The "Broken Window" Scenario
 * Player Action: In UE5, the player throws a physics object (Brick) at a window.
 * Event Log: UE5 sends a JSON payload to localhost:8000/event: { "action": "break_glass", "location": "Apt 1A", "noise_level": 90 }.
 * GM Processing: The Python Game Master queries the Vector DB for agents within "hearing range."
 * Reaction:
   * Agent A (Neighbor): Loaded with LoRA_Anxious. Receives prompt: "Loud crash next door." Output: "Hides under bed."
   * Agent B (Landlord): Loaded with LoRA_Vigilante. Output: "Grabs bat, moves to Apt 1A."
 * Result: UE5 receives instructions to spawn the Landlord NPC moving toward the player.
 Contributing
We welcome contributions! Please see CONTRIBUTING.md for details on how to train new LoRA adapters or optimize the RAG pipeline.
 License
This project is licensed under the MIT License - see the LICENSE file for details.
3. Implementation Advice
To make this functional, you need to focus on the Latency Budget.
 * Pre-fetching: Don't wait for the player to press "Talk." When the player enters a 3-meter radius of an NPC, the system should pre-load that NPC's LoRA adapter into VRAM so conversation can be instant.
 * Memory Management: SQLite-vec is fast, but ensure your embedding model (e.g., all-MiniLM-L6-v2) runs locally and is kept in memory to avoid cold-start delays.
 * Orchestration: Use the Semantic Kernel SDK for the "Game Master." It handles the function calling (e.g., determining which tool to use—waking up a neighbor vs. calling the police) much better than raw API calls.
