"""Ivy input adapter: speech, gesture, and palette clicks -> InputEvent queue.

Developer B can reuse parse_ivy_message() with an event consumer. The callbacks
only enqueue events; the controller should run in one consumer thread.
"""

from queue import Empty, Queue

from ivy.std_api import IvyBindMsg, IvyInit, IvyStart, IvyStop

from fusion_engine.event_parser import (
    CLICK_PATTERN,
    GESTURE_PATTERN,
    SPEECH_PATTERN,
    parse_ivy_message,
)
from fusion_engine.events import InputEvent

IVY_BUS = "127.255.255.255:2010"
event_queue: Queue[InputEvent] = Queue()


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


def main() -> None:
    IvyInit("FusionAdapter", "FusionAdapter Ready")
    IvyBindMsg(on_palette_click, CLICK_PATTERN)
    IvyBindMsg(on_gesture, GESTURE_PATTERN)
    IvyBindMsg(on_speech, SPEECH_PATTERN)
    IvyStart(IVY_BUS)
    print("[IVY] Connected; listening for pointing, gesture, speech")
    try:
        while True:
            # Timeout permits Ctrl+C on Windows while waiting for messages.
            try:
                event = event_queue.get(timeout=0.5)
            except Empty:
                continue
            print(f"[EVENT] {event}")
            # Later: pass this event to Developer B's controller.on_event(event).
    except KeyboardInterrupt:
        print("\n[IVY] Stopping...")
    finally:
        IvyStop()


if __name__ == "__main__":
    main()
