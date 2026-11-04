import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from fusion_engine.event_parser import parse_ivy_message


GRAMMAR_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "sra5"
    / "fusion_sra5_sapi.grxml"
)

NS = "{http://www.w3.org/2001/06/grammar}"


def load_grammar_commands():
    """Extract spoken phrases and semantic outputs from GrXML."""

    root = ET.parse(GRAMMAR_PATH).getroot()
    commands = []

    for item in root.findall(f".//{NS}item"):
        phrase = (item.text or "").strip()
        tag = item.find(f"{NS}tag")

        assert tag is not None, f"Missing semantic tag: {phrase}"

        match = re.fullmatch(
            r'\s*out\s*=\s*"([^"]+)"\s*;\s*',
            tag.text or "",
        )

        assert match is not None, (
            f"Invalid semantic tag for '{phrase}': {tag.text!r}"
        )

        commands.append((phrase, match.group(1)))

    assert commands, "No speech commands found"
    return commands


@pytest.mark.parametrize(
    "phrase, semantics",
    load_grammar_commands(),
)
def test_sra5_command_compatible_with_parser(phrase, semantics):
    """Every grammar output must be recognized by our parser."""

    message = (
        f"sra5 Parsed={semantics} "
        f"Confidence=0.95 NP=0 Num_A=0"
    )

    event = parse_ivy_message(message, received_at=10.0)

    assert event is not None, (
        f"Unrecognized speech command: {phrase}"
    )

    assert event.modality == "speech"
    assert event.kind == "speech.command"
    assert event.payload


def test_required_multimodal_phrases():
    """Verify the semantic meaning of important commands."""

    commands = dict(load_grammar_commands())

    expected = {
        "crée un cercle de cette couleur": {
            "action": "create",
            "shape": "circle",
            "color_ref": True,
        },
        "crée un cercle ici de cette couleur": {
            "action": "create",
            "shape": "circle",
            "position_ref": True,
            "color_ref": True,
        },
        "crée un cercle de cette couleur ici": {
            "action": "create",
            "shape": "circle",
            "position_ref": True,
            "color_ref": True,
        },
        "crée un rectangle vert": {
            "action": "create",
            "shape": "rectangle",
            "color": "green",
        },
        "déplace cet objet ici": {
            "action": "move",
            "target_ref": True,
            "position_ref": True,
        },
    }

    for phrase, payload in expected.items():
        assert phrase in commands, f"Missing phrase: {phrase}"

        message = (
            f"sra5 Parsed={commands[phrase]} "
            f"Confidence=0.95 NP=0 Num_A=0"
        )

        event = parse_ivy_message(message)
        assert event is not None
        assert event.payload == payload