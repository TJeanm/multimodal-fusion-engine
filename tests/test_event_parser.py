"""Run from repository root: python -m pytest -q"""

from fusion_engine.event_parser import parse_ivy_message


def test_click() -> None:
    event = parse_ivy_message("Palette Click X=600 Y=396", received_at=12.5)
    assert event is not None
    assert event.modality == "pointing"
    assert event.kind == "pointing.click"
    assert event.payload == {"x": 600, "y": 396}
    assert event.received_at == 12.5
    assert event.confidence is None


def test_gesture_french_and_decimal_comma() -> None:
    event = parse_ivy_message("OneDollarIvy Template=Cercle Confidence=0,95")
    assert event is not None
    assert event.modality == "gesture"
    assert event.payload == {"shape": "circle"}
    assert event.confidence == 0.95


def test_gesture_action() -> None:
    event = parse_ivy_message("OneDollarIvy Template=Move Confidence=0.80")
    assert event is not None
    assert event.payload == {"action": "move"}


def test_speech_structured() -> None:
    event = parse_ivy_message(
        "sra5 Parsed=action=create shape=circle color=red position_ref=true "
        "Confidence=0,92 NP=0 Num_A=0"
    )
    assert event is not None
    assert event.modality == "speech"
    assert event.kind == "speech.command"
    assert event.payload == {
        "action": "create", "shape": "circle", "color": "red", "position_ref": True
    }
    assert event.confidence == 0.92


def test_speech_quoted_action() -> None:
    event = parse_ivy_message("sra5 Parsed='creer' Confidence=0,8 NP=0 Num_A=0")
    assert event is not None
    assert event.payload == {"action": "create"}


def test_speech_move_ref() -> None:
    event = parse_ivy_message("sra5 Parsed=action=deplacer target_ref=true Confidence=0.91")
    assert event is not None
    assert event.payload == {"action": "move", "target_ref": True}


def test_unrecognized_templates_ignored() -> None:
    assert parse_ivy_message("OneDollarIvy Template=Unknown Confidence=0.55") is None


def test_unrecognized_speech_ignored() -> None:
    assert parse_ivy_message("sra5 Parsed=banana Confidence=0.8") is None


def test_out_of_range_confidence_ignored() -> None:
    assert parse_ivy_message("OneDollarIvy Template=Cercle Confidence=1.7") is None


def test_bad_message_ignored() -> None:
    assert parse_ivy_message("hello world") is None
