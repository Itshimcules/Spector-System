# LoRA Adapters Directory

This directory stores Low-Rank Adaptation (LoRA) personalities. Each character
is described by two files that share a base name (the archetype):

- `<archetype>.json` — **metadata** (traits, rank/alpha, base model). Committed
  to the repo; small and human-readable.
- `<archetype>.lora` — **trained weights**. Large and git-ignored
  (see `.gitignore`); created by training and *not* present in a fresh clone.

## Shipped adapters

| File base            | Character        | Traits                          |
|----------------------|------------------|---------------------------------|
| `grumpy_baker`       | Martha Quinn     | irritable, perfectionist        |
| `corrupt_cop`        | Officer Martinez | cynical, opportunistic          |
| `anxious_student`    | Emily Chen       | nervous, conflict-averse        |
| `vigilante_landlord` | Vincent Russo    | protective, aggressive          |

The names here must match the `lora_adapter` field for each agent in
`ai-core/config/agents.yaml` (e.g. `lora_adapter: "grumpy_baker.lora"`).

## Mock mode (no downloads)

The `LoRASwitcher` degrades gracefully. If an adapter's `.lora` weights are
absent, it loads the `.json` metadata only and serves mock responses — so the
full pipeline runs on a fresh clone with no model files. An adapter is only
treated as *missing* (and raises) when **neither** the weights nor the metadata
sidecar exist.

## Creating / training adapters

- Regenerate metadata-only mocks: `cd tools && python3 train_lora.py --create-mocks`
- Build a training dataset: `python3 train_lora.py --create-dataset`
- Real training (GPU + PEFT) is on the roadmap; trained `.lora` files drop in
  here and are picked up automatically in place of the mocks.

## Expected format (trained weights)

LoRA adapters should be compatible with the base Llama-3-8B model and loadable
via the PEFT library.
