"""
RAG Engine - Memory Retrieval System
Full-text search over episodic memories using SQLite FTS5
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval engine using SQLite FTS5 for text search
    Falls back gracefully when embedding models aren't available
    """
    
    def __init__(self, db_path: str = "memory/vector_db/spector.db"):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def store_memory(self, agent_id: str, event_description: str,
                    event_type: str = "observation",
                    location: str = None,
                    importance_score: float = 0.5) -> int:
        """Store episodic memory"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO episodic_memory 
                (agent_id, event_type, event_description, location, importance_score)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, event_type, event_description, location, importance_score))
            
            memory_id = cursor.lastrowid
            self.conn.commit()
            logger.debug(f"Stored memory {memory_id} for agent {agent_id}")
            return memory_id
        except sqlite3.Error as e:
            logger.error(f"Failed to store memory: {e}")
            self.conn.rollback()
            raise
    
    def retrieve_memories(self, query: str, agent_id: Optional[str] = None,
                         top_k: int = 5,
                         importance_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Full-text search for relevant memories
        Uses LIKE for basic keyword matching
        """
        cursor = self.conn.cursor()
        
        sql = """
            SELECT *
            FROM episodic_memory
            WHERE importance_score >= ?
            AND event_description LIKE ?
        """
        
        params = [importance_threshold, f"%{query}%"]
        
        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)
        
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(top_k)
        
        try:
            results = cursor.execute(sql, params).fetchall()
            return [dict(row) for row in results]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    def get_agent_context(self, agent_id: str, current_event: str,
                         max_memories: int = 5) -> Dict[str, Any]:
        """Get comprehensive context for an agent"""
        memories = self.retrieve_memories(
            query=current_event,
            agent_id=agent_id,
            top_k=max_memories
        )
        
        cursor = self.conn.cursor()
        
        try:
            relationships = cursor.execute("""
                SELECT 
                    CASE 
                        WHEN agent_id_1 = ? THEN agent_id_2
                        ELSE agent_id_1
                    END as other_agent,
                    relationship_type,
                    trust_level
                FROM relationships
                WHERE agent_id_1 = ? OR agent_id_2 = ?
                ORDER BY last_interaction DESC
                LIMIT 5
            """, (agent_id, agent_id, agent_id)).fetchall()
            
            agent = cursor.execute("""
                SELECT * FROM agents WHERE id = ?
            """, (agent_id,)).fetchone()
            
            return {
                'agent': dict(agent) if agent else None,
                'relevant_memories': memories,
                'relationships': [dict(r) for r in relationships],
                'emotional_state': agent['emotional_state'] if agent else 'neutral'
            }
        except sqlite3.Error as e:
            logger.error(f"Failed to get agent context: {e}")
            return {
                'agent': None,
                'relevant_memories': [],
                'relationships': [],
                'emotional_state': 'neutral'
            }
    
    def store_object(self, object_id: str, name: str, description: str,
                    location: str, significance_score: float = 0.0) -> None:
        """Store a world object"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO world_objects
                (id, name, description, current_location, significance_score, first_mentioned_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (object_id, name, description, location, significance_score))
            
            self.conn.commit()
            logger.debug(f"Stored object: {name}")
        except sqlite3.Error as e:
            logger.error(f"Failed to store object: {e}")
            self.conn.rollback()
    
    def find_relevant_objects(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find objects relevant to query using text search"""
        cursor = self.conn.cursor()
        
        try:
            results = cursor.execute("""
                SELECT *
                FROM world_objects
                WHERE description LIKE ? OR name LIKE ?
                ORDER BY significance_score DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", top_k)).fetchall()
            
            return [dict(row) for row in results]
        except sqlite3.Error as e:
            logger.error(f"Failed to find objects: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    rag = RAGEngine()
    
    memory_id = rag.store_memory(
        agent_id="student_01",
        event_description="Heard a loud crash from apartment next door",
        event_type="observation",
        location="apartment_1a",
        importance_score=0.8
    )
    
    print(f"Stored memory ID: {memory_id}")
    
    results = rag.retrieve_memories(
        query="crash",
        agent_id="student_01"
    )
    
    print(f"\nFound {len(results)} memories")
    for mem in results:
        print(f"  - {mem['event_description']}")
    
    rag.close()
