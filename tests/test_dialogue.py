from fusion_engine.dialogue_controller import DialogueController, DialogueState
from fusion_engine.events import InputEvent, PaletteCommand


def speech(t, **payload):
    return InputEvent("speech", "speech.command", payload, t)


def gesture(t, **payload):
    return InputEvent("gesture", "gesture.recognized", payload, t)


def click(t):
    return InputEvent(
        "pointing", "pointing.click",
        {"x": 200, "y": 180}, t
    )


def test_speech_then_pointing():
    controller = DialogueController()

    assert controller.on_event(
        speech(10, action="create", shape="circle", position_ref=True)
    ) == []

    assert controller.on_event(click(11)) == [
        PaletteCommand("create", "circle", 200, 180)
    ]


def test_pointing_then_speech():
    controller = DialogueController()

    assert controller.on_event(click(10)) == []

    assert controller.on_event(
        speech(11, action="create", shape="circle", position_ref=True)
    ) == [
        PaletteCommand("create", "circle", 200, 180)
    ]


def test_speech_and_gesture():
    controller = DialogueController(default_position=(300, 250))

    assert controller.on_event(speech(10, action="create")) == []

    assert controller.on_event(gesture(11, shape="diamond")) == [
        PaletteCommand("create", "diamond", 300, 250)
    ]


def test_speech_alone():
    controller = DialogueController()

    assert controller.on_event(
        speech(10, action="create", shape="circle")
    ) == []


def test_gesture_alone():
    controller = DialogueController()

    assert controller.on_event(gesture(10, shape="circle")) == []


def test_expired_pointing():
    controller = DialogueController()

    controller.on_event(click(10))

    assert controller.on_event(
        speech(15, action="create", shape="circle", position_ref=True)
    ) == []


def test_conflicting_shapes():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle")
    )

    assert controller.on_event(
        gesture(11, shape="triangle")
    ) == []
    assert controller.state == DialogueState.IDLE
    assert controller.last_rejection_reason == "conflicting_shape"


def test_here_requires_click():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", position_ref=True)
    )

    assert controller.on_event(
        gesture(11, shape="circle")
    ) == []

    assert controller.on_event(click(12)) == [
        PaletteCommand("create", "circle", 200, 180)
    ]


def test_reset_after_execution():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle", position_ref=True)
    )
    controller.on_event(click(11))

    assert controller.state == DialogueState.IDLE
    assert controller.on_event(click(12)) == []


def test_color_reference_not_implemented():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle", color_ref=True)
    )

    assert controller.on_event(click(11)) == []


def test_dialogue_window_does_not_slide():
    controller = DialogueController(window_s=4.0)

    assert controller.on_event(
        speech(10, action="create", shape="circle", position_ref=True)
    ) == []

    assert controller.on_event(
        gesture(13, shape="circle")
    ) == []

    # Too late relative to the first event (t=10).
    assert controller.on_event(click(14.5)) == []

    # The late click starts a new dialogue.
    assert controller.started_at == 14.5


def test_dialogue_timeout_on_tick():
    controller = DialogueController(window_s=4.0)

    controller.on_event(
        speech(10, action="create", shape="circle", position_ref=True)
    )

    assert controller.state == DialogueState.COLLECTING

    controller.on_tick(14.0)
    assert controller.state == DialogueState.COLLECTING

    controller.on_tick(14.1)
    assert controller.state == DialogueState.IDLE
    assert controller.started_at is None
    assert controller.buffer.get_events(14.1) == []


def test_new_dialogue_after_expiration():
    controller = DialogueController(window_s=4.0)

    controller.on_event(
        speech(10, action="create", shape="circle", position_ref=True)
    )

    # Previous dialogue has expired.
    assert controller.on_event(click(15)) == []

    # The new speech can combine with the recent click.
    assert controller.on_event(
        speech(16, action="create", shape="circle", position_ref=True)
    ) == [
        PaletteCommand("create", "circle", 200, 180)
    ]

    assert controller.state == DialogueState.IDLE
    assert controller.started_at is None


def click_at(t, x, y):
    return InputEvent(
        "pointing",
        "pointing.click",
        {"x": x, "y": y},
        t,
    )


def test_move_speech_then_clicks():
    controller = DialogueController()

    assert controller.on_event(
        speech(10, action="move", shape="rectangle")
    ) == []

    assert controller.on_event(
        click_at(11, 100, 150)
    ) == []

    assert controller.on_event(
        click_at(12, 300, 250)
    ) == [
        PaletteCommand(
            "move", "rectangle", 300, 250,
            from_x=100, from_y=150,
        )
    ]


def test_move_clicks_then_speech():
    controller = DialogueController()

    controller.on_event(click_at(10, 100, 150))
    controller.on_event(click_at(11, 300, 250))

    assert controller.on_event(
        speech(12, action="move", shape="rectangle")
    ) == [
        PaletteCommand(
            "move", "rectangle", 300, 250,
            from_x=100, from_y=150,
        )
    ]


def test_move_with_gesture():
    controller = DialogueController()

    controller.on_event(
        gesture(10, action="move", shape="triangle")
    )
    controller.on_event(click_at(11, 100, 150))

    assert controller.on_event(
        click_at(12, 300, 250)
    ) == [
        PaletteCommand(
            "move", "triangle", 300, 250,
            from_x=100, from_y=150,
        )
    ]


def test_move_missing_destination():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="move", shape="rectangle")
    )

    assert controller.on_event(
        click_at(11, 100, 150)
    ) == []


def test_move_with_color_filter():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="move", shape="rectangle", color="red")
    )
    controller.on_event(click_at(11, 100, 150))

    assert controller.on_event(
        click_at(12, 300, 250)
    ) == [
        PaletteCommand(
            "move", "rectangle", 300, 250,
            color="red",
            from_x=100, from_y=150,
        )
    ]


def test_move_conflicting_shapes():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="move", shape="rectangle")
    )
    controller.on_event(click_at(11, 100, 150))
    controller.on_event(gesture(11.5, shape="circle"))

    assert controller.on_event(
        click_at(12, 300, 250)
    ) == []


def test_move_timeout():
    controller = DialogueController(window_s=4.0)

    controller.on_event(
        speech(10, action="move", shape="rectangle")
    )
    controller.on_event(click_at(12, 100, 150))

    assert controller.on_event(
        click_at(14.5, 300, 250)
    ) == []



def test_conflicting_actions_cancel_dialogue():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle")
    )

    assert controller.on_event(
        gesture(11, action="move")
    ) == []

    assert controller.state == DialogueState.IDLE
    assert controller.started_at is None
    assert controller.last_rejection_reason == "conflicting_action"
    assert controller.buffer.get_events(11) == []


def test_conflicting_colors_cancel_dialogue():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle", color="red")
    )

    assert controller.on_event(
        speech(11, color="blue")
    ) == []

    assert controller.state == DialogueState.IDLE
    assert controller.last_rejection_reason == "conflicting_color"


def test_conflict_does_not_reuse_old_clicks():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="move", shape="rectangle")
    )

    controller.on_event(
        click_at(11, 100, 150)
    )

    assert controller.on_event(
        gesture(12, shape="triangle")
    ) == []

    assert controller.state == DialogueState.IDLE
    assert controller.last_rejection_reason == "conflicting_shape"

    # A fresh dialogue cannot reuse the old source click.
    assert controller.on_event(
        click_at(13, 300, 250)
    ) == []

    assert controller.on_event(
        speech(14, action="move", shape="rectangle")
    ) == []


def test_consistent_semantics_are_not_rejected():
    controller = DialogueController()

    assert controller.on_event(
        speech(10, action="create", shape="circle")
    ) == []

    assert controller.on_event(
        gesture(11, shape="circle")
    ) == [
        PaletteCommand("create", "circle", 400, 300)
    ]

    assert controller.state == DialogueState.IDLE
    assert controller.last_rejection_reason is None

def test_move_this_object_without_shape():
    controller = DialogueController()

    assert controller.on_event(
        speech(
            10,
            action="move",
            target_ref=True,
            position_ref=True,
        )
    ) == []

    assert controller.on_event(
        click_at(11, 100, 150)
    ) == []

    assert controller.on_event(
        click_at(12, 300, 250)
    ) == [
        PaletteCommand(
            "move", "any", 300, 250,
            from_x=100, from_y=150,
        )
    ]


def test_move_this_object_reverse_order():
    controller = DialogueController()

    controller.on_event(click_at(10, 100, 150))
    controller.on_event(click_at(11, 300, 250))

    assert controller.on_event(
        speech(
            12,
            action="move",
            target_ref=True,
            position_ref=True,
        )
    ) == [
        PaletteCommand(
            "move", "any", 300, 250,
            from_x=100, from_y=150,
        )
    ]


def test_move_without_shape_or_target():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="move")
    )
    controller.on_event(click_at(11, 100, 150))

    # No shape and no explicit target reference.
    assert controller.on_event(
        click_at(12, 300, 250)
    ) == []


def test_color_lookup_request():
    controller = DialogueController()

    assert controller.on_event(
        speech(10, action="create", shape="circle", color_ref=True)
    ) == []

    assert controller.on_event(click_at(11, 220, 160)) == []

    assert controller.state == DialogueState.COLOR_LOOKUP

    request = controller.pending_color_request

    assert request is not None
    assert request.request_id == 1
    assert request.x == 220
    assert request.y == 160


def test_color_lookup_reverse_order():
    controller = DialogueController()

    assert controller.on_event(click_at(10, 220, 160)) == []

    assert controller.on_event(
        speech(11, action="create", shape="circle", color_ref=True)
    ) == []

    assert controller.state == DialogueState.COLOR_LOOKUP
    assert controller.pending_color_request is not None


def test_color_lookup_timeout():
    controller = DialogueController(window_s=4.0)

    controller.on_event(
        speech(10, action="create", shape="circle", color_ref=True)
    )
    controller.on_event(click_at(11, 220, 160))

    assert controller.state == DialogueState.COLOR_LOOKUP

    controller.on_tick(14.5)

    assert controller.state == DialogueState.IDLE
    assert controller.pending_color_request is None


def test_combined_color_and_position_refs_wait():
    controller = DialogueController()

    controller.on_event(
        speech(
            10,
            action="create",
            shape="circle",
            color_ref=True,
            position_ref=True,
        )
    )

    assert controller.on_event(click_at(11, 220, 160)) == []

    # Click roles are not yet distinguishable.
    assert controller.pending_color_request is None
    assert controller.state == DialogueState.COLLECTING

def test_color_lookup_result_creates_shape():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle", color_ref=True)
    )
    controller.on_event(click_at(11, 220, 160))

    request = controller.pending_color_request
    assert request is not None

    assert controller.on_color_result(
        request.request_id, "red", 11.5
    ) == [
        PaletteCommand("create", "circle", 400, 300, color="red")
    ]

    assert controller.state == DialogueState.IDLE
    assert controller.pending_color_request is None


def test_color_lookup_wrong_request_id():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle", color_ref=True)
    )
    controller.on_event(click_at(11, 220, 160))

    request = controller.pending_color_request
    assert request is not None

    assert controller.on_color_result(
        request.request_id + 1, "red", 11.5
    ) == []

    assert controller.state == DialogueState.COLOR_LOOKUP
    assert controller.pending_color_request == request


def test_color_lookup_late_response():
    controller = DialogueController(window_s=4.0)

    controller.on_event(
        speech(10, action="create", shape="circle", color_ref=True)
    )
    controller.on_event(click_at(11, 220, 160))

    request = controller.pending_color_request
    assert request is not None

    assert controller.on_color_result(
        request.request_id, "red", 14.5
    ) == []

    assert controller.state == DialogueState.IDLE
    assert controller.pending_color_request is None


def test_color_lookup_ambiguous_response():
    controller = DialogueController()

    controller.on_event(
        speech(10, action="create", shape="circle", color_ref=True)
    )
    controller.on_event(click_at(11, 220, 160))

    request = controller.pending_color_request
    assert request is not None

    assert controller.on_color_result(
        request.request_id, "ambiguous", 11.5
    ) == []

    assert controller.state == DialogueState.IDLE
    assert controller.last_rejection_reason == "color_lookup_failed"


def test_color_lookup_without_pending_request():
    controller = DialogueController()

    assert controller.on_color_result(99, "blue", 10) == []
    assert controller.state == DialogueState.IDLE

