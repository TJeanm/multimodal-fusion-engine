from dataclasses import dataclass
from typing import Any, Literal

Modality = Literal["speech", "gesture", "pointing"]
EventKind = Literal[
    "speech.command",
    "gesture.recognized",
    "pointing.click",
]


@dataclass(frozen=True)
class InputEvent:
    modality: Modality
    kind: EventKind
    payload: dict[str, Any]
    received_at: float
    confidence: float | None = None


@dataclass(frozen=True)
class PaletteCommand:
    action: Literal["create", "move"]
    shape: Literal[
        "circle", "rectangle", "triangle", "diamond", "any"
    ]
    x: int
    y: int
    color: Literal["red", "green", "blue"] | None = None
    from_x: int | None = None
    from_y: int | None = None