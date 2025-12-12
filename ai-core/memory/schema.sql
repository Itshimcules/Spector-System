-- SQLite Schema for Project Spector Memory Database
-- Uses FTS5 for full-text search instead of vector embeddings

PRAGMA journal_mode=WAL;

-- NPC Agents Table
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    archetype TEXT NOT NULL,
    lora_adapter TEXT NOT NULL,
    personality_traits TEXT,
    backstory TEXT,
    voice_id TEXT,
    current_location TEXT,
    current_activity TEXT,
    emotional_state TEXT DEFAULT 'neutral',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Episodic Memory Table
CREATE TABLE IF NOT EXISTS episodic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    location TEXT,
    other_agents TEXT,
    importance_score REAL DEFAULT 0.5,
    emotional_impact TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- World Objects Table
CREATE TABLE IF NOT EXISTS world_objects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    current_location TEXT NOT NULL,
    owner_agent_id TEXT,
    significance_score REAL DEFAULT 0.0,
    first_mentioned_at TIMESTAMP,
    last_interacted_at TIMESTAMP,
    interaction_count INTEGER DEFAULT 0,
    metadata TEXT,
    FOREIGN KEY (owner_agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

-- Relationships Table
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id_1 TEXT NOT NULL,
    agent_id_2 TEXT NOT NULL,
    relationship_type TEXT,
    trust_level REAL DEFAULT 0.5,
    last_interaction TIMESTAMP,
    interaction_count INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (agent_id_1) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id_2) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE(agent_id_1, agent_id_2)
);

-- Event Log for Game Master
CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    location TEXT,
    instigator_id TEXT,
    affected_agents TEXT,
    event_data TEXT,
    resolution TEXT,
    FOREIGN KEY (instigator_id) REFERENCES agents(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_episodic_memory_agent ON episodic_memory(agent_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memory_timestamp ON episodic_memory(timestamp);
CREATE INDEX IF NOT EXISTS idx_episodic_memory_importance ON episodic_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_world_objects_location ON world_objects(current_location);
CREATE INDEX IF NOT EXISTS idx_world_objects_significance ON world_objects(significance_score);
CREATE INDEX IF NOT EXISTS idx_relationships_agents ON relationships(agent_id_1, agent_id_2);
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp ON event_log(timestamp);

-- Trigger to update agent updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_agent_timestamp 
AFTER UPDATE ON agents
BEGIN
    UPDATE agents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- View for recent high-importance memories
CREATE VIEW IF NOT EXISTS important_memories AS
SELECT 
    em.*,
    a.name as agent_name,
    a.archetype
FROM episodic_memory em
JOIN agents a ON em.agent_id = a.id
WHERE em.importance_score > 0.7
ORDER BY em.timestamp DESC;
