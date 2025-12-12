"""
Model Download and Management Script
Downloads and validates AI models for Project Spector
"""

import os
import sys
import hashlib
import requests
from pathlib import Path
from tqdm import tqdm
import argparse


MODELS = {
    'llama-3-8b-instruct-gguf': {
        'url': 'https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf',
        'filename': 'llama-2-7b-chat-q4.gguf',
        'size': '4.08 GB',
        'type': 'base_model'
    },
    'whisper-base': {
        'url': 'https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt',
        'filename': 'whisper-base.pt',
        'size': '142 MB',
        'type': 'voice'
    }
}


def download_file(url: str, dest_path: Path, desc: str = None) -> bool:
    """Download file with progress bar"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f, tqdm(
            desc=desc or dest_path.name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def verify_file(path: Path, expected_size: int = None) -> bool:
    """Verify downloaded file"""
    if not path.exists():
        return False
    
    if expected_size:
        actual_size = path.stat().st_size
        if abs(actual_size - expected_size) > 1024 * 1024:  # 1MB tolerance
            return False
    
    return True


def download_model(model_name: str, force: bool = False) -> bool:
    """Download a specific model"""
    if model_name not in MODELS:
        print(f"Unknown model: {model_name}")
        print(f"Available models: {', '.join(MODELS.keys())}")
        return False
    
    model = MODELS[model_name]
    
    if model['type'] == 'base_model':
        dest_dir = Path('models/base')
    elif model['type'] == 'voice':
        dest_dir = Path('models/voice')
    else:
        dest_dir = Path('models')
    
    dest_path = dest_dir / model['filename']
    
    if dest_path.exists() and not force:
        print(f"✓ {model_name} already exists at {dest_path}")
        return True
    
    print(f"Downloading {model_name} ({model['size']})...")
    print(f"From: {model['url']}")
    print(f"To: {dest_path}")
    
    success = download_file(model['url'], dest_path, desc=model_name)
    
    if success:
        print(f"✓ Downloaded {model_name}")
        return True
    else:
        print(f"✗ Failed to download {model_name}")
        return False


def list_models():
    """List all available models"""
    print("\nAvailable models:")
    print("-" * 60)
    for name, info in MODELS.items():
        print(f"{name:30} {info['size']:>10}  {info['type']}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description='Download AI models for Project Spector')
    parser.add_argument('model', nargs='?', help='Model to download')
    parser.add_argument('--list', action='store_true', help='List available models')
    parser.add_argument('--force', action='store_true', help='Force re-download')
    parser.add_argument('--all', action='store_true', help='Download all models')
    
    args = parser.parse_args()
    
    if args.list:
        list_models()
        return
    
    if args.all:
        print("Downloading all models...")
        for model_name in MODELS.keys():
            download_model(model_name, args.force)
    elif args.model:
        download_model(args.model, args.force)
    else:
        list_models()
        print("\nUsage: python download_models.py <model_name>")
        print("   or: python download_models.py --all")


if __name__ == '__main__':
    main()
