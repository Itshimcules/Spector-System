# Inference Benchmarks

The project's central bet is **"one brain, many masks"**: a single quantized
base model portraying the whole cast by hot-swapping LoRA personality adapters,
locally, fast enough for a game. That claim only means something with numbers.
This page is where they go, and `tools/bench_inference.py` is how you get them.

> **Status: harness built, numbers pending.** The benchmark script runs anywhere
> (it self-describes with no model present), but real figures require a GPU and
> model files, which the development sandbox does not have. Run it on your
> hardware and paste the table below.

## What it measures

Per adapter, against a fixed prompt set:

| Metric | Why it matters |
|---|---|
| **Swap (ms)** | Cost of hot-swapping a personality. If this is high, "many masks" is a lie — you'd be reloading models, not swapping adapters. |
| **First token (ms)** | Responsiveness for streaming dialogue. The number a player feels. |
| **Tokens/s** | Throughput; sets how long a full 1–2 sentence line takes. |
| **Peak VRAM (MB)** | The decider. A shipped game already wants the GPU; this is what's left for the renderer. On an 8 GB card it likely doesn't fit alongside a modern game — which is the whole feasibility question. |

It also records whether the installed llama.cpp supports **runtime** adapter
swapping (cheap) or whether it had to **reload** the model per adapter (the
swap time then includes load — an upper bound).

## How to run

```bash
# 1. Optional ML deps (compiles llama-cpp-python; needs a toolchain)
pip install -r ai-core/requirements-ml.txt

# 2. Get a quantized base model (example: Llama-3-8B Instruct, Q4_K_M GGUF)
#    e.g. from a GGUF release on Hugging Face, into ai-core/models/base/

# 3. Convert each trained LoRA to GGUF (llama.cpp ships convert_lora_to_gguf.py)
#    and drop the *.lora/*.gguf adapters into ai-core/models/loras/

# 4. Sweep all adapters
python3 tools/bench_inference.py \
    --model ai-core/models/base/llama-3-8b-instruct.Q4_K_M.gguf \
    --lora-dir ai-core/models/loras \
    --runs 5 --max-tokens 64 \
    --out tools/bench_results.json
```

Harness self-check (no model, runs anywhere):

```bash
python3 tools/bench_inference.py --dry-run
```

## Results

_Paste output from `bench_inference.py` here, one block per machine._

```
Model: <…>.gguf  |  device: gpu  |  runtime swap: <true|false>  |  peak VRAM: <…> MB

| Adapter            | Swap (ms) | First token (ms) | Tokens/s |
|--------------------|----------:|-----------------:|---------:|
| (base)             |         — |                — |        — |
| grumpy_baker       |         — |                — |        — |
| corrupt_cop        |         — |                — |        — |
| anxious_student    |         — |                — |        — |
| vigilante_landlord |         — |                — |        — |
```

**Hardware:** _GPU model, VRAM, driver_
**Model / quant:** _e.g. Llama-3-8B Instruct, Q4_K_M_

## How to read the result

- **Swap ≪ generation time** and **runtime swap = true** → "many masks" holds;
  adapter switching is effectively free next to generation.
- **First token < ~300 ms** with streaming → conversation feels responsive.
- **Peak VRAM + your game's VRAM budget < card VRAM** → it can ship co-resident.
  If not, the realistic options are a smaller model, a beefier minimum spec, or
  cloud — the trade-off discussed in the whitepaper's status section.
