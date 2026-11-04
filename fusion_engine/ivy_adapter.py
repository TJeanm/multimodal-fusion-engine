"""Ivy input adapter: speech, gesture, and palette clicks -> InputEvent queue.

Developer B can reuse parse_ivy_message() with an event consumer. The callbacks
only enqueue events; the controller should run in one consumer thread.
"""

from dataclasses import dataclass
from queue import Empty, Queue

import time

from ivy.std_api import IvySendMsg
from fusion_engine.dialogue_controller import DialogueController
from fusion_engine.events import PaletteCommand

from ivy.std_api import IvyBindMsg, IvyInit, IvyStart, IvyStop

from fusion_engine.event_parser import (
    CLICK_PATTERN,
    GESTURE_PATTERN,
    SPEECH_PATTERN,
    parse_ivy_message,
)
from fusion_engine.events import InputEvent

IVY_BUS = "127.255.255.255:2010"
COLOR_REPLY_PATTERN = (
    r"^Palette ColorAt RequestId=(\d+) "
    r"Color=(rouge|vert|bleu|none|ambiguous)$"
)

FR_TO_EN = {
    "rouge": "red",
    "vert": "green",
    "bleu": "blue",
}


@dataclass(frozen=True)
class ColorReply:
    request_id: int
    color: str
    received_at: float


event_queue: Queue[InputEvent | ColorReply] = Queue()


def _queue(raw: str) -> None:
    event = parse_ivy_message(raw)
    if event is None:
        print(f"[IGNORED] {raw}")
        return
    event_queue.put(event)


def on_palette_click(agent, x: str, y: str) -> None:
    _queue(f"Palette Click X={x} Y={y}")


def on_gesture(agent, template: str, confidence: str) -> None:
    _queue(f"OneDollarIvy Template={template} Confidence={confidence}")


def on_speech(agent, semantics: str, confidence: str) -> None:
    _queue(f"sra5 Parsed={semantics} Confidence={confidence}")

def on_palette_color(agent, request_id: str, color: str) -> None:
    event_queue.put(
        ColorReply(
            request_id=int(request_id),
            color=FR_TO_EN.get(color, color),
            received_at=time.monotonic(),
        )
    )

SHAPES = {
    "circle": "cercle",
    "rectangle": "rectangle",
    "triangle": "triangle",
    "diamond": "losange",
    "any": "any",
}

COLORS = {
    "red": "rouge",
    "green": "vert",
    "blue": "bleu",
}


def encode_command(command: PaletteCommand) -> str:
    shape = SHAPES[command.shape]

    if command.action == "create":
        message = (
            f"Fusion Create={shape} "
            f"X={command.x} Y={command.y}"
        )

    elif command.action == "move":
        message = (
            f"Fusion Move Shape={shape} "
            f"FromX={command.from_x} FromY={command.from_y} "
            f"ToX={command.x} ToY={command.y}"
        )

    else:
        raise ValueError(f"Unsupported action: {command.action}")

    if command.color is not None:
        message += f" Color={COLORS[command.color]}"

    return message

def main() -> None:
    IvyInit("FusionAdapter", "FusionAdapter Ready")

    IvyBindMsg(on_palette_click, CLICK_PATTERN)
    IvyBindMsg(on_gesture, GESTURE_PATTERN)
    IvyBindMsg(on_speech, SPEECH_PATTERN)
    IvyBindMsg(on_palette_color, COLOR_REPLY_PATTERN)

    IvyStart(IVY_BUS)

    controller = DialogueController(window_s=8.0)
    print("[IVY] Connected; listening for pointing, gesture, speech, color")

    try:
        while True:
            try:
                event = event_queue.get(timeout=0.1)

            except Empty:
                controller.on_tick(time.monotonic())
                continue

            if isinstance(event, ColorReply):
                print(
                    f"[COLOR] RequestId={event.request_id} "
                    f"Color={event.color}"
                )

                commands = controller.on_color_result(
                    event.request_id,
                    event.color,
                    event.received_at,
                )

            else:
                print(f"[EVENT] {event}")

                previous_request = controller.pending_color_request
                commands = controller.on_event(event)

                request = controller.pending_color_request

                if request is not None and request != previous_request:
                    message = (
                        f"Fusion GetColor X={request.x} "
                        f"Y={request.y} RequestId={request.request_id}"
                    )

                    IvySendMsg(message)
                    print(f"[QUERY] {message}")

            for command in commands:
                message = encode_command(command)
                IvySendMsg(message)
                print(f"[COMMAND] {message}")

    except KeyboardInterrupt:
        print("\n[IVY] Stopping...")

    finally:
        IvyStop()


if __name__ == "__main__":
    main()
