from enum import Enum

from fusion_engine.events import InputEvent, PaletteCommand
from fusion_engine.fusion_buffer import FusionBuffer


class DialogueState(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"


class DialogueController:
    """First iteration: multimodal CREATE, no Ivy dependency."""

    def __init__(
        self,
        window_s: float = 4.0,
        default_position: tuple[int, int] = (400, 300),
    ) -> None:
        self.buffer = FusionBuffer(window_s)
        self.default_position = default_position
        self.state = DialogueState.IDLE

    def on_event(self, event: InputEvent) -> list[PaletteCommand]:
        self.buffer.add(event)
        events = self.buffer.get_events(event.received_at)
        self.state = DialogueState.COLLECTING

        command = self._try_create(events)

        if command is None:
            return []

        self.reset()
        return [command]

    def on_tick(self, now: float) -> None:
        """Expire pending events even when no new input arrives."""
        if self.buffer.get_events(now):
            self.state = DialogueState.COLLECTING
        else:
            self.state = DialogueState.IDLE

    def reset(self) -> None:
        self.buffer.clear()
        self.state = DialogueState.IDLE

    def _try_create(
        self, events: list[InputEvent]
    ) -> PaletteCommand | None:

        semantic = [
            e for e in events
            if e.kind in ("speech.command", "gesture.recognized")
        ]
        spoken = [e for e in semantic if e.kind == "speech.command"]
        clicks = [e for e in events if e.kind == "pointing.click"]

        actions = {
            e.payload["action"]
            for e in semantic if "action" in e.payload
        }
        if actions != {"create"}:
            return None

        shapes = {
            e.payload["shape"]
            for e in semantic if "shape" in e.payload
        }
        valid_shapes = {"circle", "rectangle", "triangle", "diamond"}

        if len(shapes) != 1 or not shapes <= valid_shapes:
            return None

        colors = {
            e.payload["color"]
            for e in spoken if "color" in e.payload
        }
        if len(colors) > 1 or not colors <= {"red", "green", "blue"}:
            return None

        # Color lookup and object targeting are not implemented yet.
        if any(
            e.payload.get("color_ref") or e.payload.get("target_ref")
            for e in spoken
        ):
            return None

        # Multiple clicks cannot be resolved in this first version.
        if len(clicks) > 1:
            return None

        # "Here" requires actual pointing.
        if any(e.payload.get("position_ref") for e in spoken) and not clicks:
            return None

        contributing = {
            e.modality for e in semantic
            if any(k in e.payload for k in ("action", "shape"))
        }
        if clicks:
            contributing.add("pointing")

        # Never execute a monomodal user command.
        if len(contributing) < 2:
            return None

        x, y = (
            (clicks[0].payload["x"], clicks[0].payload["y"])
            if clicks else self.default_position
        )

        return PaletteCommand(
            action="create",
            shape=next(iter(shapes)),
            x=x,
            y=y,
            color=next(iter(colors), None),
        )