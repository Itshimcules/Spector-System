# LoRA Adapters Directory

This directory stores Low-Rank Adaptation (LoRA) files for character personalities.

## File Naming Convention

- `baker.lora` - Grumpy baker personality
- `cop.lora` - Corrupt police officer
- `student.lora` - Anxious student
- `landlord.lora` - Vigilante landlord
- ... (add more as needed)

## Training New Adapters

Use the training script: `tools/train_lora.sh <archetype_name>`

Each adapter should be ~50-200MB and trained on character-specific dialogue examples.

## Expected Format

LoRA adapters should be compatible with the base Llama-3-8B model and loadable via PEFT library.
