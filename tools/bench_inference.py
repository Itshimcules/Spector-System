#!/usr/bin/env python3
"""
Inference benchmark harness for the "one brain, many masks" claim.

This is the script that turns the central architectural bet into measured
numbers. Point it at a base GGUF model and a set of LoRA adapters and it reports,
per adapter:

  * adapter swap time   - how long hot-swapping a personality costs
  * first-token latency  - responsiveness for streaming dialogue
  * tokens / second      - throughput
  * peak VRAM            - the number that decides whether it can sit alongside
                           a running game on a consumer GPU

It degrades gracefully: with no model present (e.g. CI or a laptop) it prints
exactly what it would measure and emits an empty results template, so the harness
itself is verifiable anywhere. The numbers that matter require a real GPU.

Usage
-----
    # Real run (on a machine with a GPU + model files):
    pip install -r ai-core/requirements-ml.txt
    python3 tools/bench_inference.py \
        --model models/base/llama-3-8b-instruct.Q4_K_M.gguf \
        --lora-dir models/loras \
        --runs 5 --out tools/bench_results.json

    # Harness smoke test (no model needed):
    python3 tools/bench_inference.py --dry-run
"""

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_PROMPTS = [
    "You hear a loud crash and breaking glass nearby. React in character.",
    "A stranger asks you for directions to the bakery. Respond.",
    "Someone accuses you of a crime you didn't commit. What do you say?",
]


# --------------------------------------------------------------------------
# VRAM sampling (best-effort; degrades to None when no GPU tooling present)
# --------------------------------------------------------------------------

def _vram_used_mb() -> Optional[float]:
    """Current VRAM used on GPU 0 in MB, or None if it can't be measured."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()
        return info.used / (1024 * 1024)
    except Exception:
        pass

    # Fallback: parse nvidia-smi if it's on PATH.
    try:
        import subprocess
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
        )
        return float(out.decode().splitlines()[0].strip())
    except Exception:
        return None


class VramTracker:
    def __init__(self):
        self.peak: Optional[float] = None

    def sample(self):
        used = _vram_used_mb()
        if used is not None:
            self.peak = used if self.peak is None else max(self.peak, used)


# --------------------------------------------------------------------------
# llama.cpp backend with runtime adapter swapping
# --------------------------------------------------------------------------

class LlamaBackend:
    """
    Wraps llama-cpp-python. Tries runtime LoRA apply/remove; falls back to
    reloading the model per adapter if the installed version lacks runtime
    swapping (in which case 'swap' time is an upper bound that includes load).
    """

    def __init__(self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = -1):
        from llama_cpp import Llama  # noqa: F401  (import-time check)

        self._Llama = Llama
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.model = Llama(
            model_path=model_path, n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers, verbose=False,
        )
        # Feature-detect the runtime swap API (name varies across versions).
        self.runtime_swap = any(
            hasattr(self.model, attr)
            for attr in ("set_lora_adapter", "lora_adapter", "_lora_adapter")
        )

    def swap_adapter(self, adapter_path: Optional[str]) -> float:
        """Apply an adapter (or the base model if None); return swap seconds."""
        start = time.perf_counter()
        if self.runtime_swap:
            try:
                # Best-effort across API variants.
                if adapter_path is None:
                    if hasattr(self.model, "reset_lora_adapter"):
                        self.model.reset_lora_adapter()
                elif hasattr(self.model, "set_lora_adapter"):
                    self.model.set_lora_adapter(adapter_path)  # type: ignore[attr-defined]
                return time.perf_counter() - start
            except Exception:
                pass  # fall through to reload

        # Fallback: reload the model with the adapter merged at load.
        kwargs = dict(
            model_path=self.model_path, n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers, verbose=False,
        )
        if adapter_path is not None:
            kwargs["lora_path"] = adapter_path
        self.model = self._Llama(**kwargs)
        return time.perf_counter() - start

    def generate(self, prompt: str, max_tokens: int) -> Dict[str, float]:
        """Run one prompt; return first-token latency (s) and tokens/sec."""
        start = time.perf_counter()
        first_token_at: Optional[float] = None
        n_tokens = 0
        for chunk in self.model.create_completion(
            prompt, max_tokens=max_tokens, temperature=0.7, stream=True
        ):
            if first_token_at is None:
                first_token_at = time.perf_counter()
            text = chunk["choices"][0].get("text", "")
            if text:
                n_tokens += 1
        end = time.perf_counter()

        first_token_s = (first_token_at - start) if first_token_at else float("nan")
        gen_s = (end - first_token_at) if first_token_at else float("nan")
        tps = (n_tokens / gen_s) if gen_s and gen_s > 0 else float("nan")
        return {"first_token_s": first_token_s, "tokens_per_s": tps}


# --------------------------------------------------------------------------
# Benchmark driver
# --------------------------------------------------------------------------

def discover_adapters(lora_dir: Optional[str], explicit: List[str]) -> Dict[str, str]:
    adapters: Dict[str, str] = {}
    for item in explicit:
        if "=" in item:
            name, path = item.split("=", 1)
        else:
            name, path = Path(item).stem, item
        adapters[name] = path
    if lora_dir:
        for p in sorted(Path(lora_dir).glob("*.lora")):
            adapters.setdefault(p.stem, str(p))
    return adapters


def run_benchmark(args) -> dict:
    prompts = DEFAULT_PROMPTS
    if args.prompts and os.path.exists(args.prompts):
        prompts = [l.strip() for l in Path(args.prompts).read_text().splitlines() if l.strip()]

    adapters = discover_adapters(args.lora_dir, args.adapters or [])

    backend = LlamaBackend(args.model, n_gpu_layers=0 if args.cpu else -1)
    vram = VramTracker()
    vram.sample()  # baseline after load

    rows = []
    # Row 0: the base model with no adapter.
    targets = [("(base)", None)] + list(adapters.items())

    for name, path in targets:
        swap_times, ftl, tps = [], [], []
        for _ in range(args.runs):
            swap_times.append(backend.swap_adapter(path))
            for prompt in prompts:
                m = backend.generate(prompt, args.max_tokens)
                vram.sample()
                ftl.append(m["first_token_s"])
                tps.append(m["tokens_per_s"])
        rows.append({
            "adapter": name,
            "swap_ms": round(statistics.mean(swap_times) * 1000, 1),
            "first_token_ms": round(statistics.mean(ftl) * 1000, 1),
            "tokens_per_s": round(statistics.mean(tps), 1),
        })

    return {
        "model": args.model,
        "backend": "llama.cpp",
        "runtime_swap": backend.runtime_swap,
        "device": "cpu" if args.cpu else "gpu",
        "peak_vram_mb": round(vram.peak, 1) if vram.peak is not None else None,
        "n_adapters": len(adapters),
        "prompts": len(prompts),
        "results": rows,
    }


def to_markdown(report: dict) -> str:
    lines = [
        f"Model: `{report['model']}`  |  device: {report['device']}  |  "
        f"runtime swap: {report['runtime_swap']}  |  "
        f"peak VRAM: {report['peak_vram_mb']} MB",
        "",
        "| Adapter | Swap (ms) | First token (ms) | Tokens/s |",
        "|---|---:|---:|---:|",
    ]
    for r in report["results"]:
        lines.append(
            f"| {r['adapter']} | {r['swap_ms']} | {r['first_token_ms']} | {r['tokens_per_s']} |"
        )
    return "\n".join(lines)


def print_dry_run():
    print("=" * 70)
    print("bench_inference.py - harness self-check (no model loaded)")
    print("=" * 70)
    print("\nThis run measured nothing because no --model was provided.")
    print("On a machine with a GPU and model files it would report, per adapter:\n")
    print("  - swap_ms         adapter hot-swap cost")
    print("  - first_token_ms  responsiveness for streaming dialogue")
    print("  - tokens_per_s    throughput")
    print("  - peak_vram_mb    VRAM headroom vs. the game's own budget\n")
    template = {
        "model": "<path-to.gguf>", "backend": "llama.cpp", "device": "gpu",
        "peak_vram_mb": None, "results": [
            {"adapter": "(base)", "swap_ms": None, "first_token_ms": None, "tokens_per_s": None},
        ],
    }
    print("Empty results template:\n")
    print(json.dumps(template, indent=2))
    print("\nProvide --model (and --lora-dir) on a GPU box for real numbers. "
          "See docs/BENCHMARKS.md.")


def main():
    parser = argparse.ArgumentParser(description="Project Spector inference benchmark")
    parser.add_argument("--model", help="Path to base GGUF model")
    parser.add_argument("--lora-dir", help="Directory of .lora adapters to sweep")
    parser.add_argument("--adapters", nargs="*", help="Explicit name=path adapters")
    parser.add_argument("--prompts", help="File with one prompt per line")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--runs", type=int, default=3, help="Repeats per adapter")
    parser.add_argument("--cpu", action="store_true", help="Force CPU (n_gpu_layers=0)")
    parser.add_argument("--out", default="tools/bench_results.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Describe the benchmark without running it")
    args = parser.parse_args()

    if args.dry_run or not args.model:
        print_dry_run()
        return 0

    if not os.path.exists(args.model):
        print(f"error: model not found: {args.model}", file=sys.stderr)
        return 1

    try:
        import llama_cpp  # noqa: F401
    except Exception:
        print("error: llama-cpp-python not installed. "
              "Run: pip install -r ai-core/requirements-ml.txt", file=sys.stderr)
        return 1

    report = run_benchmark(args)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(to_markdown(report))
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
