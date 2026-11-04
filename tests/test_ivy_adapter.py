
from queue import Queue

import pytest

import fusion_engine.ivy_adapter as adapter
from fusion_engine.dialogue_controller import DialogueController
from fusion_engine.events import PaletteCommand


@pytest.mark.parametrize(
    "command, expected",
    [
        (
            PaletteCommand("create", "circle", 300, 250),
            "Fusion Create=cercle X=300 Y=250",
        ),
        (
            PaletteCommand(
                "create", "rectangle", 200, 180, color="blue"
            ),
            "Fusion Create=rectangle X=200 Y=180 Color=bleu",
        ),
        (
            PaletteCommand(
                "move", "any", 450, 350,
                from_x=100, from_y=150,
            ),
            "Fusion Move Shape=any FromX=100 FromY=150 "
            "ToX=450 ToY=350",
        ),
        (
            PaletteCommand(
                "move", "rectangle", 450, 350,
                color="red", from_x=100, from_y=150,
            ),
            "Fusion Move Shape=rectangle FromX=100 FromY=150 "
            "ToX=450 ToY=350 Color=rouge",
        ),
    ],
)
def test_encode_command(command, expected):
    assert adapter.encode_command(command) == expected


def test_speech_and_click_callbacks(monkeypatch):
    queue = Queue()
    monkeypatch.setattr(adapter, "event_queue", queue)

    adapter.on_speech(
        None,
        "action=create shape=circle position_ref=true",
        "0.95",
    )
    adapter.on_palette_click(None, "300", "250")

    controller = DialogueController(window_s=8.0)

    assert controller.on_event(queue.get_nowait()) == []

    commands = controller.on_event(queue.get_nowait())

    assert commands == [
        PaletteCommand("create", "circle", 300, 250)
    ]

    assert adapter.encode_command(commands[0]) == (
        "Fusion Create=cercle X=300 Y=250"
    )


def test_color_lookup_callbacks(monkeypatch):
    queue = Queue()
    monkeypatch.setattr(adapter, "event_queue", queue)

    controller = DialogueController(window_s=8.0)

    adapter.on_speech(
        None,
        "action=create shape=circle color_ref=true",
        "0.95",
    )
    adapter.on_palette_click(None, "220", "160")

    assert controller.on_event(queue.get_nowait()) == []
    assert controller.on_event(queue.get_nowait()) == []

    request = controller.pending_color_request
    assert request is not None
    assert (request.x, request.y) == (220, 160)

    adapter.on_palette_color(
        None, str(request.request_id), "rouge"
    )

    reply = queue.get_nowait()

    commands = controller.on_color_result(
        reply.request_id,
        reply.color,
        reply.received_at,
    )

    assert commands == [
        PaletteCommand(
            "create", "circle", 400, 300, color="red"
        )
    ]

    assert adapter.encode_command(commands[0]) == (
        "Fusion Create=cercle X=400 Y=300 Color=rouge"
    )
