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
        self.started_at: float | None = None

    def on_event(self, event: InputEvent) -> list[PaletteCommand]:
        """Process an input event and attempt multimodal fusion."""

        # Expire the dialogue based on its first event.
        if (
            self.started_at is not None
            and event.received_at - self.started_at > self.buffer.window_s
        ):
            self.reset()

        # Start a new dialogue when receiving its first event.
        if self.started_at is None:
            self.started_at = event.received_at

        # Store the incoming event.
        self.buffer.add(event)
        events = self.buffer.get_events(event.received_at)
        self.state = DialogueState.COLLECTING

        # Attempt to create a complete multimodal command.
        command = self._try_create(events)

        if command is None:
            command = self._try_move(events)

        if command is None:
            return []

        # Reset the dialogue after successful execution.
        self.reset()
        return [command]

    def on_tick(self, now: float) -> None:
        """Cancel the dialogue when its fixed time window expires."""

        if (
            self.started_at is not None
            and now - self.started_at > self.buffer.window_s
        ):
            self.reset()

    def reset(self) -> None:
        """Clear the entire dialogue context."""

        self.buffer.clear()
        self.started_at = None
        self.state = DialogueState.IDLE

    def _try_create(
        self, events: list[InputEvent]
    ) -> PaletteCommand | None:
        """Attempt to fuse events into a CREATE command."""

        # Extract semantic events and pointing events.
        semantic = [
            e for e in events
            if e.kind in ("speech.command", "gesture.recognized")
        ]

        spoken = [
            e for e in semantic
            if e.kind == "speech.command"
        ]

        clicks = [
            e for e in events
            if e.kind == "pointing.click"
        ]

        # Validate the requested action.
        actions = {
            e.payload["action"]
            for e in semantic
            if "action" in e.payload
        }

        if actions != {"create"}:
            return None

        # Validate the requested shape.
        shapes = {
            e.payload["shape"]
            for e in semantic
            if "shape" in e.payload
        }

        valid_shapes = {
            "circle",
            "rectangle",
            "triangle",
            "diamond",
        }

        if len(shapes) != 1 or not shapes <= valid_shapes:
            return None

        # Validate explicitly spoken colors.
        colors = {
            e.payload["color"]
            for e in spoken
            if "color" in e.payload
        }

        valid_colors = {"red", "green", "blue"}

        if len(colors) > 1 or not colors <= valid_colors:
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

        # "Here" requires an actual pointing event.
        if (
            any(e.payload.get("position_ref") for e in spoken)
            and not clicks
        ):
            return None

        # Determine the modalities contributing to this command.
        contributing = {
            e.modality
            for e in semantic
            if any(
                k in e.payload
                for k in ("action", "shape")
            )
        }

        if clicks:
            contributing.add("pointing")

        # Never execute a monomodal user command.
        if len(contributing) < 2:
            return None

        # Resolve the position.
        if clicks:
            x = clicks[0].payload["x"]
            y = clicks[0].payload["y"]
        else:
            x, y = self.default_position

        # Generate the final command.
        return PaletteCommand(
            action="create",
            shape=next(iter(shapes)),
            x=x,
            y=y,
            color=next(iter(colors), None),
        )
    
    def _try_move(
        self, events: list[InputEvent]
    ) -> PaletteCommand | None:
        """Attempt to fuse events into a MOVE command."""

        semantic = [
            e for e in events
            if e.kind in ("speech.command", "gesture.recognized")
        ]

        spoken = [
            e for e in semantic
            if e.kind == "speech.command"
        ]

        clicks = [
            e for e in events
            if e.kind == "pointing.click"
        ]

        # The action must explicitly be MOVE.
        actions = {
            e.payload["action"]
            for e in semantic
            if "action" in e.payload
        }

        if actions != {"move"}:
            return None

        # The shape must be identified.
        shapes = {
            e.payload["shape"]
            for e in semantic
            if "shape" in e.payload
        }

        valid_shapes = {
            "circle", "rectangle", "triangle", "diamond"
        }

        if len(shapes) != 1 or not shapes <= valid_shapes:
            return None

        # Optional color filter must come from speech.
        colors = {
            e.payload["color"]
            for e in spoken
            if "color" in e.payload
        }

        if len(colors) > 1 or not colors <= {
            "red", "green", "blue"
        }:
            return None

        # Referenced colors require future palette integration.
        if any(e.payload.get("color_ref") for e in spoken):
            return None

        # Source and destination must both be designated.
        if len(clicks) != 2:
            return None

        # Enforce multimodal interaction.
        modalities = {
            e.modality
            for e in semantic
            if "action" in e.payload or "shape" in e.payload
        }
        modalities.add("pointing")

        if len(modalities) < 2:
            return None

        # First click selects the source, second the destination.
        source, destination = clicks

        return PaletteCommand(
            action="move",
            shape=next(iter(shapes)),
            x=destination.payload["x"],
            y=destination.payload["y"],
            color=next(iter(colors), None),
            from_x=source.payload["x"],
            from_y=source.payload["y"],
        )