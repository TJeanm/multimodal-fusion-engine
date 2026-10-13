from enum import Enum

from fusion_engine.events import InputEvent, PaletteCommand
from fusion_engine.fusion_buffer import FusionBuffer

from dataclasses import dataclass


class DialogueState(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    COLOR_LOOKUP = "color_lookup"


@dataclass(frozen=True)
class ColorLookupRequest:
    request_id: int
    x: int
    y: int


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
        self.pending_color_request: ColorLookupRequest | None = None
        self._color_request_seq = 0
        self.last_rejection_reason: str | None = None

    def on_event(self, event: InputEvent) -> list[PaletteCommand]:
        """Process an input event and attempt multimodal fusion."""

        # Expire the dialogue based on its first event.
        self.last_rejection_reason = None

        if (
            self.started_at is not None
            and event.received_at - self.started_at > self.buffer.window_s
        ):
            self.reset()

        # Do not accept new user inputs while waiting for a palette response.
        if self.state == DialogueState.COLOR_LOOKUP:
            return []
        # Start a new dialogue when receiving its first event.
        if self.started_at is None:
            self.started_at = event.received_at

        # Store the incoming event.
        self.buffer.add(event)
        events = self.buffer.get_events(event.received_at)
        self.state = DialogueState.COLLECTING

        # Reject contradictory semantic information.
        reason = self._conflict_reason(events)

        if reason is not None:
            self.reset()
            self.last_rejection_reason = reason
            return []

        # Check whether an object color must be requested.
        if self._start_color_lookup(events):
            return []
        
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
        self.last_rejection_reason = None
        self.pending_color_request = None

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

        # Resolve explicit shape or deictic target.
        if len(shapes) == 1 and shapes <= valid_shapes:
            selected_shape = next(iter(shapes))

        elif not shapes and any(
            e.payload.get("target_ref") for e in spoken
        ):
            # Shape will be determined by palette hit-testing.
            selected_shape = "any"

        else:
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
            shape=selected_shape,
            x=destination.payload["x"],
            y=destination.payload["y"],
            color=next(iter(colors), None),
            from_x=source.payload["x"],
            from_y=source.payload["y"],
        )
    

    def _conflict_reason(
        self, events: list[InputEvent]
    ) -> str | None:
        """Detect contradictory semantic values in the dialogue."""

        semantic = [
            e for e in events
            if e.kind in ("speech.command", "gesture.recognized")
        ]

        # Detect contradictory actions or shapes.
        for field in ("action", "shape"):
            values = {
                e.payload[field]
                for e in semantic
                if field in e.payload
            }

            if len(values) > 1:
                return f"conflicting_{field}"

        # Colors are only allowed to come from speech.
        spoken_colors = {
            e.payload["color"]
            for e in semantic
            if (
                e.kind == "speech.command"
                and "color" in e.payload
            )
        }

        if len(spoken_colors) > 1:
            return "conflicting_color"

        return None
    
    def _start_color_lookup(
        self, events: list[InputEvent]
    ) -> bool:
        """Start a color query for a designated source object."""

        spoken = [
            e for e in events
            if e.kind == "speech.command"
        ]

        # The user must explicitly request "this color".
        if not any(
            e.payload.get("color_ref") for e in spoken
        ):
            return False

        # Combined references need separate click-role resolution.
        if any(
            e.payload.get("position_ref")
            or e.payload.get("target_ref")
            for e in spoken
        ):
            return False

        # Do not mix a named color with a color reference.
        if any("color" in e.payload for e in spoken):
            return False

        semantic = [
            e for e in events
            if e.kind in ("speech.command", "gesture.recognized")
        ]

        actions = {
            e.payload["action"]
            for e in semantic
            if "action" in e.payload
        }

        shapes = {
            e.payload["shape"]
            for e in semantic
            if "shape" in e.payload
        }

        clicks = [
            e for e in events
            if e.kind == "pointing.click"
        ]

        valid_shapes = {
            "circle", "rectangle", "triangle", "diamond"
        }

        # This first version only queries colors for CREATE.
        if actions != {"create"}:
            return False

        if len(shapes) != 1 or not shapes <= valid_shapes:
            return False

        if len(clicks) != 1:
            return False

        # Prepare a query for the palette.
        self._color_request_seq += 1

        self.pending_color_request = ColorLookupRequest(
            request_id=self._color_request_seq,
            x=clicks[0].payload["x"],
            y=clicks[0].payload["y"],
        )

        self.state = DialogueState.COLOR_LOOKUP
        return True