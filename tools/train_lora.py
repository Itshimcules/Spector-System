"""
LoRA Training Script for Character Personalities
Creates character-specific LoRA adapters from training data
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
import yaml


# Character training templates
CHARACTER_TEMPLATES = {
    'grumpy_baker': {
        'base_traits': ['irritable', 'perfectionist', 'direct'],
        'speech_patterns': [
            'short sentences',
            'complaints about noise',
            'mentions of baking'
        ],
        'sample_responses': [
            "Can't you see I'm trying to work here?",
            "That racket is going to ruin my sourdough starter.",
            "I've been up since 4 AM making bread, and this is what I get?"
        ]
    },
    'corrupt_cop': {
        'base_traits': ['cynical', 'opportunistic', 'street-smart'],
        'speech_patterns': [
            'asks about money',
            'implies favors',
            'uses cop jargon'
        ],
        'sample_responses': [
            "I might be able to look the other way... for a price.",
            "Everything's negotiable if you know how to play the game.",
            "Been on this beat for years. Seen it all."
        ]
    },
    'anxious_student': {
        'base_traits': ['nervous', 'studious', 'conflict-averse'],
        'speech_patterns': [
            'hesitant language',
            'mentions studying',
            'worries aloud'
        ],
        'sample_responses': [
            "I... I have finals next week, I really can't deal with this.",
            "What if someone calls the police? I can't afford trouble.",
            "Maybe I should just hide and pretend I didn't hear anything?"
        ]
    },
    'vigilante_landlord': {
        'base_traits': ['protective', 'aggressive', 'paranoid'],
        'speech_patterns': [
            'territorial language',
            'military terminology',
            'protective of property'
        ],
        'sample_responses': [
            "Nobody damages my building and gets away with it.",
            "I served in the military. I can handle troublemakers.",
            "This is my property. I have every right to defend it."
        ]
    }
}


def generate_training_data(character_type: str, num_samples: int = 100) -> List[Dict]:
    """Generate synthetic training data for a character"""
    if character_type not in CHARACTER_TEMPLATES:
        raise ValueError(f"Unknown character type: {character_type}")
    
    template = CHARACTER_TEMPLATES[character_type]
    training_data = []
    
    # Use the sample responses as seed data
    for response in template['sample_responses']:
        training_data.append({
            'instruction': 'Respond to a situation in character',
            'input': 'A loud noise disturbs you',
            'output': response,
            'character': character_type
        })
    
    print(f"Generated {len(training_data)} training samples for {character_type}")
    return training_data


def create_mock_lora(character_type: str, output_dir: Path):
    """Create a mock LoRA adapter file for testing"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create metadata file
    metadata = {
        'character_type': character_type,
        'base_model': 'llama-2-7b',
        'rank': 8,
        'alpha': 16,
        'traits': CHARACTER_TEMPLATES[character_type]['base_traits'],
        'created': 'mock_adapter',
        'version': '0.1.0'
    }
    
    adapter_path = output_dir / f"{character_type}.lora"
    metadata_path = output_dir / f"{character_type}.json"
    
    # Write metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Create empty adapter file (in real version, this would be model weights)
    with open(adapter_path, 'w') as f:
        f.write(f"# Mock LoRA adapter for {character_type}\n")
        f.write(f"# Traits: {', '.join(metadata['traits'])}\n")
    
    print(f"✓ Created mock LoRA adapter: {adapter_path}")
    print(f"✓ Created metadata: {metadata_path}")


def create_training_dataset(output_file: Path):
    """Create complete training dataset for all characters"""
    all_data = []
    
    for character_type in CHARACTER_TEMPLATES.keys():
        data = generate_training_data(character_type, num_samples=20)
        all_data.extend(data)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\n✓ Created training dataset: {output_file}")
    print(f"  Total samples: {len(all_data)}")


def main():
    parser = argparse.ArgumentParser(description='LoRA training utilities')
    parser.add_argument('--create-mocks', action='store_true', help='Create mock adapters')
    parser.add_argument('--create-dataset', action='store_true', help='Create training dataset')
    parser.add_argument('--character', type=str, help='Specific character to process')
    
    args = parser.parse_args()
    
    if args.create_mocks:
        lora_dir = Path('../ai-core/models/loras')
        
        if args.character:
            create_mock_lora(args.character, lora_dir)
        else:
            for char_type in CHARACTER_TEMPLATES.keys():
                create_mock_lora(char_type, lora_dir)
    
    if args.create_dataset:
        dataset_path = Path('training_data/character_responses.json')
        create_training_dataset(dataset_path)
    
    if not (args.create_mocks or args.create_dataset):
        print("Usage:")
        print("  --create-mocks          Create mock LoRA adapters for testing")
        print("  --create-dataset        Create training dataset JSON")
        print("  --character <type>      Process specific character only")
        print(f"\nAvailable characters: {', '.join(CHARACTER_TEMPLATES.keys())}")


if __name__ == '__main__':
    main()
