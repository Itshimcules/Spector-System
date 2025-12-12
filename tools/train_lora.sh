#!/bin/bash
# LoRA Training Helper Script
# Fine-tune new character personality adapters

set -e

ARCHETYPE_NAME=${1:-"new_character"}
TRAINING_DATA=${2:-"data/training/${ARCHETYPE_NAME}.jsonl"}
OUTPUT_DIR="ai-core/models/loras"
BASE_MODEL="ai-core/models/base/llama-3-8b-quantized"

echo "🧠 Training LoRA Adapter: $ARCHETYPE_NAME"
echo "📁 Training data: $TRAINING_DATA"
echo ""

# Check if training data exists
if [ ! -f "$TRAINING_DATA" ]; then
    echo "❌ Training data not found: $TRAINING_DATA"
    echo "Expected JSONL format with prompt/completion pairs"
    exit 1
fi

# Run training (example using Hugging Face PEFT)
python - <<EOF
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
import torch

print("Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    "$BASE_MODEL",
    load_in_8bit=True,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("$BASE_MODEL")

print("Configuring LoRA...")
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)

print(f"Training on: $TRAINING_DATA")
# Add actual training code here

print(f"Saving adapter to: $OUTPUT_DIR/${ARCHETYPE_NAME}.lora")
model.save_pretrained(f"$OUTPUT_DIR/${ARCHETYPE_NAME}.lora")
print("✅ Training complete!")
EOF

echo ""
echo "📦 LoRA adapter saved: $OUTPUT_DIR/${ARCHETYPE_NAME}.lora"
echo "💡 Add to agents.yaml to use in game"
