# Project Spector

## Solving the Authoring Bottleneck: A Local-First Generative AI Architecture for Deep NPC Simulation

**Version 1.0 — June 2026**

*Project Spector Contributors*

---

## Abstract

For two decades, the immersive simulation genre has been constrained by a single economic reality: the cost of authoring deep, reactive character behavior grows faster than any studio's capacity to pay it. Warren Spector's "One City Block" concept — a game world that is small in area but unbounded in depth, where every room is enterable, every drawer openable, and every resident a fully realized character — has remained a thought experiment because hand-scripting hundreds of deeply reactive NPCs is infeasible.

Project Spector is an open-source framework that attacks this bottleneck directly. Rather than scripting behavior, it *generates* it: a single locally hosted language model portrays an entire cast of characters by hot-swapping lightweight Low-Rank Adaptation (LoRA) personality modules, an event-driven orchestration layer (the "Game Master") decides which characters perceive and react to which world events, and a persistent memory store gives every character and object a durable history. The result is a middleware architecture in which believable, consistent, emergent NPC behavior is a property of the system rather than a line item in a content budget.

This paper describes the problem, the design principles, the three-pillar architecture, the event lifecycle from game engine to generated behavior and back, the latency engineering required to make local inference game-viable, and an honest account of the current implementation status and open problems.

---

## 1. Introduction: The One City Block Vision

In a widely cited 2004 interview, Deus Ex director Warren Spector described his dream project: not a bigger world, but a deeper one.

> "A simulation where the player cannot travel for miles, but can enter every room, open every drawer, speak to every resident, and disrupt every routine."

The proposal inverts the dominant trend in open-world design. Instead of square kilometers of terrain populated by shallow, interchangeable NPCs, it asks for a single city block in which *density of simulation* replaces *breadth of geography*. Every character has a schedule, a personality, relationships, secrets, and — critically — the capacity to react coherently to anything the player does.

The vision was never realized. Not because rendering a city block is hard (it is not), but because of what we call the **Authoring Bottleneck**.

### 1.1 Why now

Three technical developments between 2023 and 2026 changed the feasibility calculus:

1. **Capable small language models.** Quantized 7–8B parameter models (e.g., Llama-3-8B at 4-bit) now run on consumer GPUs — and even CPUs — at interactive latencies, producing dialogue and behavioral reasoning that is contextually coherent.
2. **Parameter-efficient fine-tuning (LoRA).** A character's "personality" can be encoded as a Low-Rank Adapter measured in tens of megabytes, swappable at runtime, rather than as a separately hosted multi-gigabyte model.
3. **Lightweight local retrieval.** Embedded databases with full-text and vector search (SQLite FTS5, sqlite-vec) make persistent, queryable world memory available with sub-millisecond local latency and zero infrastructure.

Project Spector is the synthesis of these three developments into a single coherent game-middleware architecture.

---

## 2. The Problem: The Authoring Bottleneck

### 2.1 The combinatorics of depth

Consider a modest cast of 200 NPCs in a single city block. For each character, traditional production requires:

- **Dialogue trees** covering every topic the player may raise, in every relevant world state;
- **Behavior scripts** (state machines, behavior trees, or GOAP rule sets) covering every event the character can witness;
- **Consistency bookkeeping** so the character's reactions reflect what has already happened.

Each axis multiplies the others. A character who can react to 50 event types in 10 emotional states across 20 world-state flags is, naively, a 10,000-branch authoring problem — *per character*. Studios resolve this the only way they can: most NPCs get three bark lines and a walk cycle. Depth is reserved for a handful of plot-critical characters, and the "living world" is an ambient illusion.

### 2.2 Why scripting cannot close the gap

Scripted systems share a structural flaw: **the author must enumerate the situation in advance.** Behavior trees and GOAP planners are excellent at selecting among pre-authored actions, but they cannot improvise a response to a situation nobody anticipated. When the player does something genuinely novel — stacks furniture against a door, accuses the wrong character of a crime, returns a stolen item three in-game days later — scripted NPCs fail silently, and the simulation's credibility collapses at exactly the moment the player is most engaged.

### 2.3 Why cloud LLM-NPC services are not the answer for this problem

Several commercial services (notably in the 2023–2025 wave of "AI NPC" middleware) place character cognition in cloud-hosted models. This works for dialogue but is poorly matched to *simulation*:

- **Latency:** A simulation tick that requires a 300–900 ms network round-trip per NPC reaction cannot drive ambient world behavior.
- **Cost:** Per-token pricing across hundreds of NPCs reacting to continuous world events is economically unbounded for the player or the studio.
- **Availability and shippability:** A boxed or offline game cannot depend on a third-party inference endpoint existing in ten years.
- **Privacy and modding:** Local inference keeps player data on-device and lets modders train and distribute their own characters.

Project Spector therefore commits to **local-first inference** as a foundational constraint, and derives its architecture from the consequences of that constraint.

---

## 3. Design Principles

1. **Depth over breadth.** The framework targets a small, dense space — one block, dozens to hundreds of agents — not an open world. Every design trade favors per-agent richness over agent count.
2. **One brain, many masks.** It is infeasible to run hundreds of concurrent LLMs; it is unnecessary. A single base model with hot-swapped personality adapters portrays the full cast.
3. **Events, not polling.** NPCs do not "think" continuously. Cognition is *provoked* by world events whose relevance is computed centrally. Idle NPCs cost nothing.
4. **Memory is the world.** Consistency — the property that separates a character from a chatbot — comes from a persistent, queryable store of episodic memory, object history, and relationships, injected into every generation.
5. **Engine-agnostic middleware.** The AI core is a self-contained service speaking JSON over HTTP. Unreal Engine 5 is the reference client, but nothing in the architecture is engine-specific.
6. **Graceful degradation.** Every AI component (LLM, STT, TTS, adapters) has a deterministic mock fallback. The framework is fully developable and testable on a laptop with no model files and no GPU.

---

## 4. System Architecture

The system is a client–service pair. The game engine owns rendering, physics, animation, and player input; the AI core owns cognition, memory, and speech. They communicate through a small REST API (FastAPI, four endpoints).

```
┌──────────────────────────┐
│   Game Engine (UE5)      │   rendering · physics · input
│   C++ AIAPIClient        │   animation · navigation
└────────────┬─────────────┘
             │  JSON / HTTP
             ▼
┌─────────────────────────────────────────────────┐
│              AI Core (FastAPI, Python)          │
│                                                 │
│  ┌──────────────┐   Pillar 1: Causal Engine    │
│  │ Game Master  │   semantic radius, wake       │
│  └──────┬───────┘   probability, prompt build   │
│         │                                       │
│  ┌──────▼───────┐   Pillar 2: Hive Mind        │
│  │LoRA Switcher │   one base LLM, hot-swapped   │
│  │ + LLM Engine │   personality adapters (LRU)  │
│  └──────┬───────┘                               │
│         │                                       │
│  ┌──────▼───────┐   Pillar 3: Infinite Drawer  │
│  │  RAG Engine  │   episodic memory, object     │
│  │  (SQLite)    │   history, relationships      │
│  └──────────────┘                               │
│                                                 │
│  ┌──────────────┐                               │
│  │Voice Service │   Whisper STT · Piper TTS     │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

### 4.1 Pillar 1 — The Game Master (Causal Engine)

The Game Master is the simulation's attention mechanism, modeled on the "Concordia" pattern of a central narrator-orchestrator coordinating independent agents. It answers the question scripting answers with triggers: *who notices what?*

When the engine reports an event, the Game Master:

1. **Computes a semantic radius** — how far the event's influence plausibly reaches. Radii are configured per event class (in the reference configuration: `violence` reaches 20 m with wake probability 1.0; `loud_noise` 15 m at 0.9; `property_damage` 10 m at 0.8; `conversation` 5 m at 0.7) with a noise-level fallback for unclassified events.
2. **Selects affected agents** by intersecting agent positions with the radius and sampling each agent's wake probability. An anxious student two rooms away wakes for a gunshot but not for a conversation on the street.
3. **Assembles a per-agent prompt** combining the agent's identity (name, archetype, personality traits, backstory), the event description, and retrieved context from the memory layer.
4. **Logs the event** to the persistent event log, so the world's history accretes.

The decisive property is that event *meaning*, not event *scripting*, drives propagation. The author defines event classes and characters; the system derives the reactions. Adding a 50th event type or a 200th character does not multiply authoring work — it adds one row to a configuration file.

Each agent also carries a daily schedule (location and activity by time of day), giving the Game Master a baseline of normal behavior from which disruptions — the heart of the One City Block fantasy — deviate.

### 4.2 Pillar 2 — The Hive Mind (LoRA Personality Switching)

Running 200 concurrent 8B-parameter models would require terabytes of memory. Project Spector instead runs **one** quantized base model (reference target: Llama-3-8B, 4-bit GGUF via llama.cpp) and represents each character as a **LoRA adapter** — a low-rank delta on the base weights, tens of megabytes rather than gigabytes — plus a JSON metadata sidecar describing traits and voice.

The LoRA Switcher manages this cast:

- **LRU cache.** A bounded set of adapters stays resident; the least recently used is evicted when a new character speaks. Cache statistics are tracked for tuning.
- **Predictive prefetch.** The engine reports player proximity, and adapters for nearby characters are loaded *before* interaction begins, hiding swap latency entirely in the common case.
- **Uniform generation interface.** The Game Master requests "a reaction from `vigilante_landlord` to this prompt"; the switcher resolves the adapter, ensures it is loaded, and runs inference.

The reference cast demonstrates the pattern with four archetypes: Martha Quinn (grumpy baker — irritable, perfectionist), Officer Jake Martinez (corrupt cop — cynical, opportunistic), Emily Chen (anxious student — nervous, conflict-averse), and Vincent Russo (vigilante landlord — protective, aggressive, ex-military). Each is fully defined by an adapter, a metadata file, a schedule, and a backstory — the marginal cost of a new character is a fine-tuning run, not a writing and scripting team.

### 4.3 Pillar 3 — The Infinite Drawer (Persistent Memory and Retrieval)

Generation without memory produces chatbots, not characters. The RAG Engine gives every agent and object a durable history in an embedded SQLite database (WAL mode, full-text search now; `sqlite-vec` embedding search planned), with five core tables:

| Table | Stores | Role in simulation |
|---|---|---|
| `agents` | Identity, traits, location, activity, emotional state | The living cast |
| `episodic_memory` | Timestamped events each agent experienced, with importance and emotional-impact scores | What a character *knows* |
| `world_objects` | Every significant object: location, owner, significance, interaction history | Chekhov's Gun bookkeeping |
| `relationships` | Pairwise trust levels, interaction counts, relationship type | Social fabric |
| `event_log` | Global causal record of all Game Master events | World history / debugging |

Importance scoring lets retrieval favor memorable events over noise (a curated `important_memories` view surfaces high-importance entries), and significance scoring on objects means a locket mentioned once in passing can resurface, correctly contextualized, hours of play later. This is the mechanism behind narrative consistency: when an NPC speaks, the prompt is grounded in *what actually happened in this player's world*, not in the model's general priors.

The store is deliberately local and embedded: zero infrastructure, sub-millisecond queries, trivially included in a save file.

### 4.4 The Voice Layer

A deep simulation invites spoken interaction. The voice service wraps **Whisper** for speech-to-text and **Piper** for text-to-speech, with per-character voice identities (`voice_id` in agent metadata). Both run locally, consistent with the local-first constraint, and both degrade gracefully: absent model files, STT returns placeholder transcriptions and TTS emits valid (silent) WAV containers, so the full pipeline remains exercisable in development.

### 4.5 Engine Integration

The reference client is an Unreal Engine 5 C++ module (`AIAPIClient`) handling HTTP transport and JSON serialization, with a Blueprint-facing interface so designers can wire game events to the AI core without C++. The API surface is intentionally small:

- `POST /event` — report a world event; receive affected agents and their generated reactions.
- `POST /dialogue` — player speaks to an NPC; receive in-character text, synthesized audio, and emotional state.
- `GET /agents`, `GET /agent/{id}` — cast roster and per-agent state/context.

Because the contract is four JSON endpoints, integration with Unity, Godot, or a custom engine is an afternoon's transport code, not a port.

---

## 5. The Event Lifecycle: "The Broken Window"

The canonical walkthrough, end to end:

1. **Player action.** In UE5, the player throws a brick through the window of Apartment 1A.
2. **Event report.** The engine POSTs to `/event`:
   ```json
   {
     "event_type": "property_damage",
     "action": "break_glass",
     "location": "apartment_1a",
     "noise_level": 90,
     "event_description": "A window has been shattered by a thrown brick."
   }
   ```
3. **Orchestration.** The Game Master resolves `property_damage` → radius 10.0, wake probability 0.8; intersects with agent locations; logs the event.
4. **Cognition.** For each awakened agent, the memory layer supplies context, the LoRA Switcher mounts the right personality, and the LLM generates a reaction:
   - *Emily Chen* (`anxious_student`, at home in 1A): hides under the bed and considers calling the police — but she's afraid of Officer Martinez.
   - *Vincent Russo* (`vigilante_landlord`, doing maintenance): grabs a bat and moves toward Apartment 1A. It's *his* building.
5. **Actuation.** The engine receives structured reactions and drives navigation, animation, and dialogue. The player, still holding a second brick, sees a light go off in 1A and hears footsteps on the stairs.
6. **Persistence.** Both agents write episodic memories with high emotional impact; Russo's trust toward the player (if identified) drops; the window joins `world_objects` as broken. Tomorrow, Martha Quinn will have heard about it.

No author scripted any branch of this. The behavior is the intersection of event classification, spatial logic, personality, and memory.

---

## 6. Performance Engineering

Local inference is viable only with a strict latency budget. Measured and projected figures for the reference stack:

| Mode | Reaction latency | Memory | Hardware |
|---|---|---|---|
| Mock (development) | < 10 ms | < 100 MB | Any |
| CPU inference (8B Q4) | 500–2000 ms | 4–8 GB RAM | Modern CPU |
| GPU inference (8B Q4) | 50–200 ms | 4–8 GB VRAM | CUDA GPU |

Four strategies keep the simulation responsive at these numbers:

1. **Asynchrony by design.** Event reactions are inherently async — an NPC taking 800 ms to "decide" to investigate a noise reads as natural human reaction time, not lag. Only direct dialogue is latency-critical, and GPU inference meets conversational expectations there.
2. **Predictive adapter prefetch.** Proximity-triggered LoRA loading removes swap cost from the interactive path.
3. **Wake-probability gating.** Most events wake few or no agents; the expensive path runs only when narratively warranted.
4. **Local retrieval.** Memory queries are embedded-database reads — microseconds, not network calls — so context assembly is effectively free relative to generation.

Targets for the integration milestone: < 500 ms ambient reaction on CPU, < 1000 ms voice round-trip, 60 FPS engine-side with the AI core on the same machine.

---

## 7. Relation to Existing Approaches

| Approach | Strength | Why it doesn't solve the bottleneck |
|---|---|---|
| Behavior trees / FSMs | Predictable, performant, tooling-mature | Every behavior must be enumerated in advance |
| GOAP / utility AI | Flexible action *selection* | Selects among authored actions; cannot improvise content |
| Cloud LLM NPC middleware | High dialogue quality | Latency, per-token cost, online dependency; dialogue-centric rather than simulation-centric |
| Generative agents (Park et al., 2023) | Demonstrated emergent multi-agent social behavior with memory + retrieval + LLMs | Research sandbox; no engine integration, no latency budget, cloud inference |

Project Spector's contribution is not any single technique — orchestrated agents, LoRA swapping, and RAG memory each exist — but their integration into **game middleware with a latency budget, an engine contract, and a content pipeline**, under a local-first constraint, aimed at a specific and previously unreachable design target.

The traditional and generative layers are complementary in practice: the engine's navigation, animation, and physics systems remain authoritative for *execution*; Spector replaces only the *decision and dialogue* layer that scripting could never scale.

---

## 8. Current Status and Limitations

Project Spector is a **functional prototype framework**, and this paper is candid about what that means.

**Implemented and tested today** (pytest suite, CI on every push):

- The full orchestration layer: event processing, semantic radius, agent selection, prompt assembly.
- The LoRA Switcher with LRU caching and prefetch, operating on adapter metadata.
- The persistent memory layer: full schema, episodic memory, objects, relationships, text search.
- The four-endpoint API, the UE5 C++ client interface, and the voice layer with mock fallbacks.
- The four-character reference cast with schedules, traits, and backstories.
- Database seeding, model download, and adapter scaffolding tools.

**Not yet integrated:**

- **Real LLM inference.** The engine architecture (llama.cpp path) exists; model weights are not bundled, and generation currently runs in character-aware mock mode. This is the active milestone.
- **Trained LoRA adapters.** Current adapters are structural placeholders; the training pipeline (dataset format and scaffolding exist) has not produced fine-tuned weights.
- **Vector embeddings.** Memory retrieval is currently FTS text search; semantic search via `sqlite-vec` is planned.
- **The 3D environment.** The UE5 client is an integration interface, not a playable demo.

**Open problems** we consider genuinely hard and unsolved, here and field-wide:

1. **Behavioral grounding.** Constraining generated *intentions* to the engine's executable action vocabulary (structured/grammar-based decoding is the planned approach).
2. **Long-horizon consistency.** Importance-scored memory mitigates but does not solve drift across tens of hours of play; memory consolidation strategies are future work.
3. **Content safety and tonal control.** A generative cast must stay within the game's rating and fiction; per-adapter guardrails and output filtering are required before any shippable use.
4. **Determinism and QA.** Testing a game whose characters improvise requires new methodology — seeded generation, behavioral property tests, and simulation replay are under consideration.
5. **Concurrency at scale.** Single-threaded event processing comfortably handles a demo cast; the 200-agent target requires batched inference and async DB work (Phase 5).

---

## 9. Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 — Foundation | Orchestration, memory, API, UE5 interface, tests/CI | **Complete** |
| 2 — AI Integration | Llama-3-8B inference, trained LoRAs, real voice, latency benchmarks | **In progress** |
| 3 — Unreal Environment | Playable city block, 4 NPCs, proximity prefetch, dialogue UI | Planned |
| 4 — Content & Polish | 10-character cast, mystery scenario, consequence and reputation systems | Planned |
| 5 — Optimization | Batched inference, 20+ concurrent agents, production hardening | Planned |
| 6 — Public Release | Packaged demo, modding documentation, community launch | Planned |

The detailed milestone breakdown lives in [`ROADMAP.md`](../ROADMAP.md).

---

## 10. Conclusion

The Authoring Bottleneck was never a creative failure; it was an economic one. Designers have known for twenty years what a deeply simulated city block should feel like — no studio could afford to write it. Project Spector's thesis is that the bottleneck is now an architecture problem, and architecture problems have engineering solutions: one local model wearing many personality masks, an orchestrator that routes attention the way a tabletop game master does, and a memory store that makes the world's history queryable at generation time.

The framework presented here is early, and Section 8 enumerates exactly how early. But the foundation — the part that determines whether the approach can work at all — is built, tested, and open source under the MIT license. We invite game developers, AI engineers, and writers to interrogate it, break it, and build on it.

**Repository:** https://github.com/Itshimcules/Spector-System

---

## References

1. Spector, W. — public interviews describing the "One City Block" RPG concept (originating c. 2004), proposing depth-dense simulation over geographic breadth.
2. Hu, E. J., et al. (2021). *LoRA: Low-Rank Adaptation of Large Language Models.* arXiv:2106.09685.
3. Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., Bernstein, M. S. (2023). *Generative Agents: Interactive Simulacra of Human Behavior.* UIST '23. arXiv:2304.03442.
4. Vezhnevets, A. S., et al. (2023). *Generative agent-based modeling with actions grounded in physical, social, or digital space using Concordia.* arXiv:2312.03664. (Origin of the "Game Master" orchestration pattern.)
5. Touvron, H., et al. / Meta AI (2024). *The Llama 3 Herd of Models.* arXiv:2407.21783.
6. Gerganov, G., et al. *llama.cpp: LLM inference in C/C++.* https://github.com/ggerganov/llama.cpp
7. Radford, A., et al. (2022). *Robust Speech Recognition via Large-Scale Weak Supervision* (Whisper). arXiv:2212.04356.
8. Rhasspy project. *Piper: a fast, local neural text-to-speech system.* https://github.com/rhasspy/piper
9. Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020. arXiv:2005.11401.

---

*This whitepaper describes Project Spector v0.1.x. Architecture and figures reflect the implementation in this repository as of June 2026; sections 6 and 8 distinguish measured behavior from design targets.*
