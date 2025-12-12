"""
FastAPI Backend - Main Entry Point
Provides REST API for Unreal Engine to communicate with AI services
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
import uvicorn

from orchestration.game_master import GameMaster
from orchestration.lora_switcher import LoRASwitcher
from orchestration.rag_engine import RAGEngine
from voice.stt_whisper import WhisperSTT
from voice.tts_piper import PiperTTS

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Project Spector AI Backend",
    version="0.1.0",
    description="AI orchestration for dynamic NPC behaviors"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

try:
    game_master = GameMaster()
    lora_switcher = LoRASwitcher(
        base_model_path="models/base/llama-3-8b-quantized",
        lora_directory="models/loras"
    )
    rag_engine = RAGEngine()
    stt_service = WhisperSTT()
    tts_service = PiperTTS()
    logger.info("All services initialized")
except Exception as e:
    logger.error(f"Service initialization failed: {e}")
    raise


# Pydantic models for request/response
class GameEvent(BaseModel):
    event_type: str
    action: str
    location: str
    noise_level: Optional[int] = 0
    event_description: str
    instigator_id: Optional[str] = "player"


class NPCDialogueRequest(BaseModel):
    npc_id: str
    player_message: str
    context: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    return {
        "service": "Project Spector AI Backend",
        "status": "online",
        "version": "1.0.0"
    }


@app.post("/event")
async def process_event(event: GameEvent):
    """
    Process a game event from Unreal Engine
    Returns affected agents and their reactions
    """
    try:
        response = game_master.process_event(event.dict())
        
        # Generate actual LLM responses for each agent
        for reaction in response['agent_reactions']:
            lora_response = lora_switcher.generate_response(
                adapter_name=reaction['lora_adapter'],
                prompt=reaction['prompt']
            )
            reaction['generated_response'] = lora_response
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dialogue")
async def npc_dialogue(request: NPCDialogueRequest):
    """
    Handle player-NPC conversation
    """
    try:
        # Get agent context from RAG
        context = rag_engine.get_agent_context(
            agent_id=request.npc_id,
            current_event=request.player_message
        )
        
        # Build prompt
        agent = context['agent']
        prompt = f"""You are {agent['name']}.
Player says: "{request.player_message}"

Respond naturally in character (1-2 sentences)."""
        
        # Generate response with appropriate LoRA
        lora_adapter = f"{agent['archetype']}.lora"
        response_text = lora_switcher.generate_response(lora_adapter, prompt)
        
        # Convert to speech
        audio = tts_service.synthesize(
            text=response_text,
            voice_id=agent.get('voice_id', 'default')
        )
        
        return {
            "npc_id": request.npc_id,
            "text_response": response_text,
            "audio_base64": audio.hex(),  # In production, use base64
            "emotional_state": agent['emotional_state']
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents():
    """List all available NPC agents"""
    return {"agents": game_master.agents_config['agents']}


@app.get("/agent/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get detailed information about a specific agent"""
    context = rag_engine.get_agent_context(agent_id, "current state")
    return context


if __name__ == "__main__":
    print("Starting Project Spector AI Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
