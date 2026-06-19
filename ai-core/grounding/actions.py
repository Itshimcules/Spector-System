"""
The game verb set - the ONLY actions an NPC can take in the world.

This is the contract between the generative core and the engine. The LLM never
hands the engine free-form text; it emits an ``AgentDecision`` whose actions are
drawn exclusively from this closed vocabulary. Anything outside it cannot be
represented, which is what makes downstream validation a hard guarantee rather
than a best effort.

Each action is a Pydantic model with a literal ``verb`` discriminator, so the
union serializes to clean JSON and compiles to a JSON-schema / GBNF grammar for
constrained decoding (see ``grammar.py``).
"""

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class MoveTo(BaseModel):
    verb: Literal["move_to"] = "move_to"
    location: str = Field(..., description="Destination location id")


class Investigate(BaseModel):
    verb: Literal["investigate"] = "investigate"
    location: str = Field(..., description="Location id to go look at")


class Say(BaseModel):
    verb: Literal["say"] = "say"
    text: str = Field(..., description="What the NPC says aloud")
    to: Optional[str] = Field(default=None, description="agent id addressed, or null")


class PickUp(BaseModel):
    verb: Literal["pick_up"] = "pick_up"
    object_id: str = Field(..., description="World object id to pick up")


class Hide(BaseModel):
    verb: Literal["hide"] = "hide"


class Flee(BaseModel):
    verb: Literal["flee"] = "flee"
    to_location: Optional[str] = Field(default=None, description="Where to flee, or null")


class CallContact(BaseModel):
    verb: Literal["call_contact"] = "call_contact"
    contact: str = Field(..., description="agent id or known external contact (e.g. police)")


class Attack(BaseModel):
    verb: Literal["attack"] = "attack"
    target_id: str = Field(..., description="agent id to attack")


class DoNothing(BaseModel):
    verb: Literal["do_nothing"] = "do_nothing"


# Discriminated union over the verb literal. Pydantic uses ``verb`` to pick the
# right model when parsing, and rejects anything that isn't one of these.
Action = Annotated[
    Union[
        MoveTo,
        Investigate,
        Say,
        PickUp,
        Hide,
        Flee,
        CallContact,
        Attack,
        DoNothing,
    ],
    Field(discriminator="verb"),
]

VERBS = {
    "move_to",
    "investigate",
    "say",
    "pick_up",
    "hide",
    "flee",
    "call_contact",
    "attack",
    "do_nothing",
}


class AgentDecision(BaseModel):
    """A single turn's worth of NPC intent: some reasoning plus ordered actions."""

    reasoning: str = Field(default="", description="Brief in-character justification")
    actions: List[Action] = Field(default_factory=list)
