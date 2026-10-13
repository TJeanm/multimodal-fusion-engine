import pytest

from fusion_engine.events import InputEvent
from fusion_engine.fusion_buffer import FusionBuffer


def make_speech_event(t: float) -> InputEvent:
    return InputEvent(
        modality="speech",
        kind="speech.command",
        payload={
            "action": "create",
            "shape": "circle",
            "position_ref": True,
        },
        received_at=t,
    )


def make_click_event(t: float) -> InputEvent:
    return InputEvent(
        modality="pointing",
        kind="pointing.click",
        payload={"x": 200, "y": 180},
        received_at=t,
    )


def test_events_within_window():
    buffer = FusionBuffer(window_s=4.0)

    buffer.add(make_speech_event(100.0))
    buffer.add(make_click_event(101.2))

    assert len(buffer.get_events(101.2)) == 2


def test_expired_events():
    buffer = FusionBuffer(window_s=4.0)

    buffer.add(make_speech_event(100.0))
    buffer.add(make_click_event(106.0))

    events = buffer.get_events(106.0)

    assert len(events) == 1
    assert events[0].modality == "pointing"


def test_clear_buffer():
    buffer = FusionBuffer()

    buffer.add(make_speech_event(100.0))
    buffer.clear()

    assert buffer.get_events(101.0) == []


def test_invalid_window():
    with pytest.raises(ValueError):
        FusionBuffer(window_s=-1)