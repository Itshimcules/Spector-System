# Project Spector Roadmap

## Vision

Create a fully functional AI-driven NPC simulation framework demonstrating Warren Spector's "One City Block" concept, where depth replaces breadth and every character has emergent, believable behaviors.

---

## Current Status (v0.1.0 - Prototype)

**Completed:**
- Core architecture and orchestration layer
- FastAPI backend with 4 endpoints
- Game Master event routing system
- LoRA adapter management system
- Text-based memory/RAG engine
- LLM inference engine with fallbacks
- Voice service stubs (Whisper + Piper)
- C++ Unreal Engine client interface
- 4 character personality adapters
- Model download utilities
- Database seeding tools

**What Works:**
- Event processing and agent selection
- Character-aware response generation (mock mode)
- Memory storage and retrieval
- Database operations
- Development without model downloads

---

## Phase 1: Foundation (COMPLETE)

**Goal:** Create working prototype framework

**Milestones:**
- [x] API server with CORS support
- [x] Database schema design
- [x] Event orchestration logic
- [x] LoRA cache management
- [x] Documentation and guides
- [x] Git repository setup

**Timeline:** Completed December 2025

---

## Phase 2: AI Integration (IN PROGRESS)

**Goal:** Add real AI model support

### Q1 2026

**LLM Integration**
- [x] LLM inference engine architecture
- [x] Mock mode with fallbacks
- [ ] Download Llama-3-8B model
- [ ] Benchmark inference latency
- [ ] Optimize for <500ms response time
- [ ] Add model quantization options

**LoRA System**
- [x] Mock adapter creation
- [x] Character metadata system
- [ ] Create training dataset (100+ samples per character)
- [ ] Implement actual LoRA training pipeline
- [ ] Train 4 character adapters on real data
- [ ] Add adapter hot-swapping benchmarks

**Voice Services**
- [x] Service architecture with fallbacks
- [ ] Integrate Whisper model
- [ ] Integrate Piper TTS
- [ ] Test end-to-end voice latency
- [ ] Add streaming audio support
- [ ] Optimize for <1000ms round-trip

---

## Phase 3: Unreal Engine Integration (PLANNED)

**Goal:** Create playable 3D environment

### Q2 2026

**3D Environment**
- [ ] Design single city block layout
- [ ] Create basic building meshes
- [ ] Implement interior spaces (10+ rooms)
- [ ] Add physics interactions
- [ ] Lighting and atmosphere

**NPC Implementation**
- [ ] Create 4 NPC character models
- [ ] Implement Blueprint logic for AI integration
- [ ] Add animation state machines
- [ ] Implement proximity-based LoRA preloading
- [ ] Add facial expressions/lip sync

**Player Interaction**
- [ ] Movement and interaction system
- [ ] Object manipulation (drawers, doors, etc.)
- [ ] Dialogue UI
- [ ] Voice input integration
- [ ] Event triggering system

---

## Phase 4: Content & Polish (PLANNED)

**Goal:** Create compelling demo scenario

### Q3 2026

**Characters**
- [ ] Expand to 10 unique NPCs
- [ ] Create detailed backstories
- [ ] Define relationships between characters
- [ ] Add daily schedules and routines
- [ ] Train individual LoRA adapters

**Story Elements**
- [ ] Design "mystery" scenario
- [ ] Place Chekhov's Gun items
- [ ] Create branching narrative possibilities
- [ ] Add consequence system
- [ ] Implement reputation tracking

**Environment Details**
- [ ] Add 50+ interactive objects
- [ ] Create object history/memory
- [ ] Add ambient sounds
- [ ] Implement weather/time of day
- [ ] Add visual feedback for AI reasoning

---

## Phase 5: Optimization & Testing (PLANNED)

**Goal:** Production-ready system

### Q4 2026

**Performance**
- [ ] Profile and optimize AI inference
- [ ] Add GPU acceleration support
- [ ] Implement batch processing for multiple NPCs
- [ ] Optimize memory usage
- [ ] Target 60 FPS in Unreal

**Testing**
- [ ] Unit tests for all modules
- [ ] Integration tests for full pipeline
- [ ] Stress test with 20+ active NPCs
- [ ] User testing sessions
- [ ] Bug fixing and refinement

**Production Features**
- [ ] Add authentication to API
- [ ] Implement rate limiting
- [ ] Add structured logging
- [ ] Create monitoring dashboard
- [ ] Write deployment guide

---

## Phase 6: Public Release (PLANNED)

**Goal:** Share with community

### Q1 2027

**Documentation**
- [ ] Complete API documentation
- [ ] Video tutorials
- [ ] Developer guides
- [ ] Modding documentation
- [ ] Performance tuning guide

**Community**
- [ ] Create Discord server
- [ ] Set up GitHub Discussions
- [ ] Write blog post/announcement
- [ ] Submit to relevant forums (r/gamedev, etc.)
- [ ] Create showcase video

**Distribution**
- [ ] Package demo build
- [ ] Create installer/setup script
- [ ] Provide pre-trained models (if licensing allows)
- [ ] Set up CDN for model downloads
- [ ] Create itch.io page

---

## Feature Wishlist (Future)

**Advanced AI**
- Multi-modal LLMs (vision + language)
- Emotion recognition from voice
- Procedural animation generation
- Long-term memory consolidation
- Cross-NPC emergent storytelling

**Gameplay**
- Multiplayer support
- Procedural city block generation
- Modding API
- Character creator
- Save/load system

**Technical**
- Cloud deployment option
- WebGL/browser version
- Mobile platform support
- VR compatibility
- Real-time collaboration tools

---

## Success Metrics

**Phase 2 (AI Integration)**
- LLM inference <500ms on CPU
- Voice round-trip <1000ms
- 4 distinct character personalities

**Phase 3 (Unreal Integration)**
- Playable demo with 4 NPCs
- Every room enterable
- Smooth 60 FPS performance

**Phase 4 (Content)**
- 10 unique characters
- 30-minute playthrough
- Multiple story outcomes

**Phase 5 (Production)**
- 90%+ test coverage
- Zero critical bugs
- <100MB memory usage per NPC

**Phase 6 (Release)**
- 1000+ GitHub stars
- Active community contributions
- 10+ derivative projects

---

## Contributing

We welcome contributions at any phase:

**Current Needs:**
- LoRA training expertise
- Unreal Engine developers
- Character writers/designers
- Performance optimization
- Documentation improvements

See `CONTRIBUTING.md` for guidelines.

---

## Timeline Overview

| Phase | Timeline | Status |
|-------|----------|--------|
| Phase 1: Foundation | Dec 2024 | COMPLETE |
| Phase 2: AI Integration | Q1 2026 | IN PROGRESS |
| Phase 3: Unreal Integration | Q2 2026 | PLANNED |
| Phase 4: Content & Polish | Q3 2026 | PLANNED |
| Phase 5: Optimization | Q4 2026 | PLANNED |
| Phase 6: Public Release | Q1 2027 | PLANNED |

---

**Last Updated:** December 12, 2025  
**Current Version:** 0.1.0 (Prototype)  
**Next Milestone:** Complete AI model integration
