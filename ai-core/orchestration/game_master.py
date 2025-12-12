"""
Game Master - Concordia Pattern Implementation
Handles event orchestration and agent coordination
"""

import json
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
import yaml

class GameMaster:
    """
    The Game Master acts as the central causal engine.
    It listens to events from Unreal Engine and determines:
    1. Which agents should "wake up" and react
    2. What context they need from memory
    3. Which LoRA adapters to load
    """
    
    def __init__(self, config_path: str = "config/settings.json", 
                 agents_path: str = "config/agents.yaml"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        with open(agents_path, 'r') as f:
            self.agents_config = yaml.safe_load(f)
        
        self.active_agents = {}
        self.event_history = []
        
    def calculate_semantic_radius(self, event: Dict[str, Any]) -> float:
        """
        Calculate how far an event's influence reaches
        Based on event type and properties (noise level, violence, etc.)
        """
        event_type = event.get('event_type', 'unknown')
        wake_conditions = self.agents_config['game_master']['wake_conditions']
        
        if event_type in wake_conditions:
            return wake_conditions[event_type]['radius']
        
        # Fallback: use noise level if available
        noise_level = event.get('noise_level', 0)
        return max(5.0, noise_level / 10.0)
    
    def calculate_distance(self, loc1: str, loc2: str) -> float:
        """Calculate distance between locations"""
        if loc1 == loc2:
            return 0.0
        return 10.0
    
    def get_affected_agents(self, event: Dict[str, Any]) -> List[str]:
        """
        Determine which agents should react to an event
        Returns list of agent IDs that fall within semantic radius
        """
        event_location = event.get('location', '')
        radius = self.calculate_semantic_radius(event)
        affected = []
        
        for agent in self.agents_config['agents']:
            agent_location = agent.get('current_location', '')
            distance = self.calculate_distance(event_location, agent_location)
            
            if distance <= radius:
                # Check wake probability
                event_type = event.get('event_type', 'unknown')
                wake_conditions = self.agents_config['game_master']['wake_conditions']
                
                if event_type in wake_conditions:
                    wake_prob = wake_conditions[event_type]['wake_probability']
                    if wake_prob > 0.5:
                        affected.append(agent['id'])
        
        return affected
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main event processing pipeline:
        1. Calculate affected agents
        2. Retrieve relevant memories for each agent
        3. Generate prompts for LoRA inference
        4. Return orchestrated response
        """
        self.event_history.append({
            'timestamp': datetime.now().isoformat(),
            'event': event
        })
        
        affected_agents = self.get_affected_agents(event)
        
        response = {
            'event_id': len(self.event_history),
            'timestamp': datetime.now().isoformat(),
            'affected_agents': affected_agents,
            'agent_reactions': []
        }
        
        for agent_id in affected_agents:
            agent_data = next((a for a in self.agents_config['agents'] 
                             if a['id'] == agent_id), None)
            
            if agent_data:
                reaction = {
                    'agent_id': agent_id,
                    'agent_name': agent_data['name'],
                    'lora_adapter': agent_data['lora_adapter'],
                    'prompt': self._generate_prompt(agent_data, event),
                    'context': self._get_agent_context(agent_id)
                }
                response['agent_reactions'].append(reaction)
        
        return response
    
    def _generate_prompt(self, agent_data: Dict, event: Dict) -> str:
        """
        Generate contextual prompt for the agent based on event
        """
        personality = ', '.join(agent_data.get('personality_traits', []))
        
        prompt = f"""You are {agent_data['name']}, a {agent_data['archetype']}.
Personality: {personality}
Backstory: {agent_data['backstory']}

Current situation: {event.get('event_description', 'An event has occurred nearby.')}
Location: {event.get('location', 'Unknown')}

How do you react? Consider your personality and current emotional state.
Respond with your immediate thought/action (1-2 sentences).
"""
        return prompt
    
    def _get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """Retrieve relevant context for agent"""
        return {
            'recent_memories': [],
            'current_emotional_state': 'neutral',
            'relationships': []
        }
    
    def get_agent_schedule(self, agent_id: str, time: str) -> Optional[Dict]:
        """
        Check what an agent should be doing at a given time
        Useful for determining baseline behavior
        """
        agent_data = next((a for a in self.agents_config['agents'] 
                          if a['id'] == agent_id), None)
        
        if not agent_data or 'schedule' not in agent_data:
            return None
        
        for schedule_item in agent_data['schedule']:
            return schedule_item
        
        return None


if __name__ == "__main__":
    # Example usage
    gm = GameMaster()
    
    # Simulate "broken window" event from Unreal
    test_event = {
        'event_type': 'property_damage',
        'action': 'break_glass',
        'location': 'apartment_1a',
        'noise_level': 90,
        'event_description': 'A window has been shattered by a thrown brick.'
    }
    
    response = gm.process_event(test_event)
    print(json.dumps(response, indent=2))
