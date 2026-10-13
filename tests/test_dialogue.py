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