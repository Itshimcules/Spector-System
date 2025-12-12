"""
Database Seeding Script
Initializes the SQLite database with schema and sample data
"""

import sqlite3
import json
import yaml
from pathlib import Path


def create_database():
    """Create and initialize the database"""
    db_path = Path("../ai-core/memory/vector_db/spector.db")
    schema_path = Path("../ai-core/memory/schema.sql")
    
    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating database at: {db_path}")
    
    # Connect and execute schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    print("✓ Schema created")
    
    # Load agent definitions
    agents_path = Path("../ai-core/config/agents.yaml")
    with open(agents_path, 'r') as f:
        agents_config = yaml.safe_load(f)
    
    # Insert agents
    for agent in agents_config['agents']:
        cursor.execute("""
            INSERT INTO agents (id, name, archetype, lora_adapter, 
                               personality_traits, backstory, voice_id,
                               current_location, current_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent['id'],
            agent['name'],
            agent['archetype'],
            agent['lora_adapter'],
            json.dumps(agent['personality_traits']),
            agent['backstory'],
            agent['voice_id'],
            agent['schedule'][0]['location'] if agent['schedule'] else 'unknown',
            agent['schedule'][0]['activity'] if agent['schedule'] else 'idle'
        ))
    
    print(f"✓ Inserted {len(agents_config['agents'])} agents")
    
    # Insert sample memories
    sample_memories = [
        {
            'agent_id': 'student_01',
            'event_type': 'observation',
            'description': 'Moved into apartment 1A three months ago',
            'importance': 0.6
        },
        {
            'agent_id': 'baker_01',
            'event_type': 'emotion',
            'description': 'Angry about teenagers loitering outside bakery',
            'importance': 0.7
        }
    ]
    
    for mem in sample_memories:
        cursor.execute("""
            INSERT INTO episodic_memory 
            (agent_id, event_type, event_description, importance_score)
            VALUES (?, ?, ?, ?)
        """, (mem['agent_id'], mem['event_type'], mem['description'], mem['importance']))
    
    print(f"✓ Inserted {len(sample_memories)} sample memories")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database initialization complete!")


if __name__ == "__main__":
    create_database()
