"""Convert raw Ivy messages into the shared InputEvent type.

This module intentionally does not open an Ivy connection: it can be unit-tested
without Processing, sra5, or OneDollarIvy.
"""

import re
import shlex
import time

from fusion_engine.events import InputEvent

CLICK_PATTERN = r"^Palette Click X=(\d+) Y=(\d+)$"
GESTURE_PATTERN = (
    r"^OneDollarIvy Template=(\S+) Confidence=([0-9]+(?:[.,][0-9]+)?)$"
)
SPEECH_PATTERN = (
    r"^sra5 Parsed=(.*?) Confidence=([0-9]+(?:[.,][0-9]+)?)"
    r"(?: NP=\d+ Num_A=\d+)?$"
)

_CLICK = re.compile(CLICK_PATTERN)
_GESTURE = re.compile(GESTURE_PATTERN)
_SPEECH = re.compile(SPEECH_PATTERN)

_SHAPES = {
    "circle": "circle", "cercle": "circle",
    "rectangle": "rectangle", "carre": "rectangle", "carré": "rectangle",
    "triangle": "triangle", "diamond": "diamond", "losange": "diamond",
}
_ACTIONS = {"create": "create", "creer": "create", "créer": "create",
            "move": "move", "deplacer": "move", "déplacer": "move"}
_COLORS = {"red": "red", "rouge": "red", "green": "green", "vert": "green",
           "blue": "blue", "bleu": "blue"}
_TRUE = {"true", "yes", "oui", "1"}
_FALSE = {"false", "no", "non", "0"}


def _confidence(raw: str) -> float | None:
    try:
        result = float(raw.replace(",", "."))
        return result if 0 <= result <= 1 else None
    except ValueError:
        return None


def _speech_payload(raw_semantics: str) -> dict | None:
    """Interpret only agreed semantic tokens, never guess from free speech.

    Expected future GrXML semantic output e.g.:
       action=create shape=circle color=red position_ref=true
    Also accepts one-word action values such as 'creer' for smoke testing.
    """
    raw = raw_semantics.strip().strip("'\"").strip()
    try:
        tokens = shlex.split(raw)
    except ValueError:
        return None
    payload: dict = {}
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            key, value = key.lower(), value.strip("'\"").lower()
            if key == "action":
                if value not in _ACTIONS:
                    return None
                payload["action"] = _ACTIONS[value]
            elif key == "shape":
                if value not in _SHAPES:
                    return None
                payload["shape"] = _SHAPES[value]
            elif key == "color":
                if value not in _COLORS:
                    return None
                payload["color"] = _COLORS[value]
            elif key in {"position_ref", "color_ref", "target_ref"}:
                if value in _TRUE:
                    payload[key] = True
                elif value in _FALSE:
                    payload[key] = False
                else:
                    return None
            # Unrecognised additional semantic tags are ignored, not invented.
        else:
            word = token.lower()
            if word in _ACTIONS:
                payload["action"] = _ACTIONS[word]
            elif word in _SHAPES:
                payload["shape"] = _SHAPES[word]
            elif word in _COLORS:
                payload["color"] = _COLORS[word]
            elif word in {"ici", "here"}:
                payload["position_ref"] = True
    return payload or None


def parse_ivy_message(raw: str, *, received_at: float | None = None) -> InputEvent | None:
    """Parse supported raw Ivy messages; return None for unsupported input."""
    timestamp = time.monotonic() if received_at is None else received_at

    match = _CLICK.fullmatch(raw)
    if match:
        x, y = map(int, match.groups())
        return InputEvent("pointing", "pointing.click", {"x": x, "y": y}, timestamp)

    match = _GESTURE.fullmatch(raw)
    if match:
        template, raw_confidence = match.groups()
        confidence = _confidence(raw_confidence)
        if confidence is None:
            return None
        name = template.lower()
        if name in _SHAPES:
            payload = {"shape": _SHAPES[name]}
        elif name in _ACTIONS:
            payload = {"action": _ACTIONS[name]}
        else:
            return None  # Untrained/unknown template: no made-up meaning
        return InputEvent("gesture", "gesture.recognized", payload, timestamp, confidence)

    match = _SPEECH.fullmatch(raw)
    if match:
        semantic_text, raw_confidence = match.groups()
        confidence = _confidence(raw_confidence)
        payload = _speech_payload(semantic_text)
        if confidence is None or payload is None:
            return None
        return InputEvent("speech", "speech.command", payload, timestamp, confidence)

    return None
