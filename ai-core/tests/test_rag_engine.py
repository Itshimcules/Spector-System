import os
import sqlite3
import pytest
from orchestration.rag_engine import RAGEngine

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "memory", "schema.sql")


@pytest.fixture
def rag(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.close()
    engine = RAGEngine(db_path=db_path)
    yield engine
    engine.close()


def test_store_and_retrieve_memory(rag):
    memory_id = rag.store_memory(
        agent_id="student_01",
        event_description="Heard a loud crash from the apartment next door",
        event_type="observation",
        importance_score=0.8,
    )
    assert memory_id is not None

    results = rag.retrieve_memories("crash", agent_id="student_01")
    assert len(results) == 1
    assert "crash" in results[0]["event_description"]


def test_retrieve_no_results_for_unknown_query(rag):
    results = rag.retrieve_memories("xyzzy_no_match_ever")
    assert results == []


def test_retrieve_importance_threshold_filters(rag):
    rag.store_memory("agent_a", "Low priority event", importance_score=0.2)
    rag.store_memory("agent_a", "High priority event", importance_score=0.9)
    results = rag.retrieve_memories("event", importance_threshold=0.5)
    assert len(results) == 1
    assert "High priority" in results[0]["event_description"]


def test_retrieve_filters_by_agent_id(rag):
    rag.store_memory("agent_1", "Event seen by agent_1", importance_score=0.5)
    rag.store_memory("agent_2", "Event seen by agent_2", importance_score=0.5)
    results = rag.retrieve_memories("Event", agent_id="agent_1")
    assert len(results) == 1
    assert results[0]["agent_id"] == "agent_1"


def test_store_and_find_object(rag):
    rag.store_object(
        object_id="gpu_01",
        name="GPU Tray",
        description="A removable GPU tray in rack 3",
        location="rack_3",
        significance_score=0.6,
    )
    results = rag.find_relevant_objects("GPU Tray")
    assert len(results) == 1
    assert results[0]["name"] == "GPU Tray"
    assert results[0]["current_location"] == "rack_3"


def test_find_objects_no_results(rag):
    results = rag.find_relevant_objects("nonexistent_object_xyzzy")
    assert results == []


def test_get_agent_context_unknown_agent(rag):
    context = rag.get_agent_context("nonexistent_agent", "some event")
    assert context["agent"] is None
    assert context["relevant_memories"] == []
    assert context["relationships"] == []
    assert context["emotional_state"] == "neutral"
