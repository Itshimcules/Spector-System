"""
Constrained-decoding grammar for AgentDecision.

The JSON schema of the action vocabulary is compiled to a GBNF grammar that
llama.cpp enforces *during* generation. With the grammar active, the decoder is
structurally incapable of emitting a token sequence that isn't a valid
AgentDecision - the model cannot invent a verb or malform the JSON. This is the
generation-time half of the safety story; ``validator.py`` is the semantic half.

llama.cpp is optional, so this degrades gracefully: when it (or grammar support)
is unavailable, ``build_grammar`` returns ``None`` and the pipeline falls back to
parse-then-validate, which still guarantees only legal actions reach the engine.
"""

import json
import logging
from typing import Any, Optional

from .actions import AgentDecision

logger = logging.getLogger(__name__)


def decision_json_schema() -> dict:
    """JSON schema for a full AgentDecision (usable by any schema enforcer)."""
    return AgentDecision.model_json_schema()


def build_grammar() -> Optional[Any]:
    """
    Return a ``llama_cpp.LlamaGrammar`` enforcing the AgentDecision schema, or
    ``None`` if llama.cpp / grammar support isn't available.
    """
    try:
        from llama_cpp import LlamaGrammar
    except Exception:
        logger.debug("llama_cpp unavailable; generation will be unconstrained")
        return None

    try:
        return LlamaGrammar.from_json_schema(json.dumps(decision_json_schema()))
    except Exception as e:  # pragma: no cover - depends on llama_cpp internals
        logger.warning(f"Could not build grammar from schema: {e}")
        return None
