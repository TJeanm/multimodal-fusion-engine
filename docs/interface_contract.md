# Multimodal Fusion Engine — Interface Contract

**Version:** 0.1 (design proposal)  
**Project:** UPSSITECH 5A SRI — Multimodal Fusion  
**Scope:** Interface between input adapters, the Python fusion engine, and the Processing palette.

> **Implementation status:** Only the `Fusion Create=<shape> X=<x> Y=<y>` palette command is implemented and has been manually tested. Every other wire message below is a proposed extension, not an existing feature. Both contributors must approve changes to the shared contract before implementation.

## 1. Architecture and responsibilities

```text
sra5 / speech simulator ────┐
OneDollarIvy / gestures ───┼───── Ivy ──> Python input adapters ──> InputEvent queue
Palette mouse clicks ──────┘                                         │
                                                                     v
                                              FusionBuffer + DialogueController
                                                                     │
                                                                     v
                                                PaletteCommand / Ivy output adapter
                                                                     │
                                                                     v
                                                        Processing palette
```

**Developer A — adapters and palette:** Ivy subscriptions, provider-specific parsing, `InputEvent` production, speech/gesture simulator, palette clicks, palette command execution, speech/gesture tool integration.

**Developer B — fusion and dialogue:** `FusionBuffer`, dialogue FSM, timeout logic, semantic validation, command creation, pure unit tests.

**Shared ownership:** this contract, canonical values, end-to-end scenarios, FSM and chronograms. Neither developer changes the shared event model or wire format without notifying the other.

## 2. Transport and naming

- **Ivy address:** `127.255.255.255:2010` (local development).
- **Raw messages:** one line of plain text; no JSON transport requirement.
- **Canonical internal terms:** English, lowercase: `create`, `move`; shapes `circle`, `rectangle`, `triangle`, `diamond`; colors `red`, `green`, `blue`.
- **Palette wire terms:** French, lowercase: `cercle`, `rectangle`, `triangle`, `losange`; colors `rouge`, `vert`, `bleu`.
- **Point coordinates:** integer pixels in Processing canvas coordinates, origin at top left; validate against current canvas bounds, which may change when the palette window is resized.
- **Regex-friendly protocol:** preserve fixed field names and order in messages below. An omitted optional field must not be included as `None`.
- **Confidence:** normalized float between 0 and 1, or `None` if unavailable. Raw recognizer messages may use either `0.8` or `0,8`; adapters normalize the decimal separator.

## 3. Incoming Ivy messages (raw / external)

| Producer | Message example | Status | Adapter output |
| --- | --- | --- | --- |
| `sra5` or speech simulator | `sra5 Parsed='creer' Confidence=0,8 NP=0 Num_A=0` | Format prescribed by course; `Parsed` content depends on the team's GrXML grammar | `speech.command` |
| OneDollarIvy | `OneDollarIvy Template=Rectangle Confidence=0.92` | Format in the official Processing source; gesture names depend on trained templates | `gesture.recognized` |
| Processing palette | `Palette Click X=200 Y=180` | **Proposed; to implement** in `mousePressed()` | `pointing.click` |

The `sra5` sample semantic token `creer` is illustrative: the actual tokens must match the agreed speech grammar. Preserve the provider's original raw message in logs to make debugging possible.

**Important:** when integrated, pointer clicks should be **reported** to the fusion engine rather than directly and silently changing a shape's color. The existing palette's local keyboard/mouse shortcuts may remain available in a separate development/demo mode.

## 4. Python internal event contract (shared between A and B)

Put the type and canonical values in **`fusion_engine/events.py`**, merged into `main` before parallel feature work.

```python
from dataclasses import dataclass, field
from typing import Any, Literal

Modality = Literal["speech", "gesture", "pointing"]
EventKind = Literal["speech.command", "gesture.recognized", "pointing.click"]

@dataclass(frozen=True)
class InputEvent:
    modality: Modality
    kind: EventKind
    payload: dict[str, Any]
    received_at: float             # time.monotonic() at adapter reception
    confidence: float | None = None
```

**Payload schema (enforce in each adapter):**

| `kind` | Required payload keys | Optional payload keys | Example |
| --- | --- | --- | --- |
| `speech.command` | At least one recognized semantic item | `action`, `shape`, `color`, `position_ref`, `color_ref`, `target_ref` | `{"action": "create", "shape": "circle", "color": "red", "position_ref": True}` |
| `gesture.recognized` | One of `shape` or `action` | — | `{"shape": "circle"}` |
| `pointing.click` | `x`, `y` | — | `{"x": 200, "y": 180}` |

`position_ref` means the utterance contains **"here" / "ici"**, requiring a real pointing event. `color_ref` means **"this color" / "de cette couleur"**, requiring a pointing event plus a color lookup. `target_ref` means a deictic target (**"ce/cet objet"**) requiring target selection by pointing.

Events may represent partial information: `{"action": "create"}` is valid. An adapter must **not** invent missing semantic fields. It must normalize recognized provider tokens, without deciding whether enough information exists to execute an operation.

**Examples:**

```python
InputEvent("speech", "speech.command",
           {"action": "create", "color": "red", "position_ref": True},
           received_at=100.0, confidence=0.92)

InputEvent("gesture", "gesture.recognized",
           {"shape": "circle"}, received_at=100.4, confidence=0.85)

InputEvent("pointing", "pointing.click",
           {"x": 200, "y": 180}, received_at=100.8)
```

**API boundary:** Developer A calls `controller.on_event(event)` (or enqueues it into a single consumer queue). Developer B exposes `on_event(event: InputEvent) -> list[PaletteCommand]`. No Processing-specific object crosses this boundary. Run the controller with one consumer/serialized event processing; Ivy callbacks should not mutate the controller directly from multiple threads.

## 5. Internal output contract

Define in **`fusion_engine/events.py`**:

```python
@dataclass(frozen=True)
class PaletteCommand:
    action: Literal["create", "move"]
    shape: Literal["circle", "rectangle", "triangle", "diamond", "any"]
    x: int                       # new position / destination
    y: int
    color: Literal["red", "green", "blue"] | None = None
    from_x: int | None = None    # required for move
    from_y: int | None = None    # required for move
```

The output adapter translates canonical English fields to the palette's French Ivy message format. `shape="any"` is legal for `move` only. A `create` with no explicit color uses the palette default (currently gray). When the user did not designate a position, `create` may use a documented default position **only if** the interaction is otherwise multimodal; explicit `position_ref=True` must wait for a click.

## 6. Outgoing Ivy messages (fusion → palette)

| Purpose | Exact wire example | Status |
| --- | --- | --- |
| Create without explicit color | `Fusion Create=cercle X=200 Y=180` | **Implemented and tested** |
| Create with spoken color | `Fusion Create=cercle X=200 Y=180 Color=rouge` | **Proposed**: palette regex, parser, and `setColor()` handling need extension |
| Move a selected object | `Fusion Move Shape=rectangle FromX=120 FromY=150 ToX=350 ToY=280` | **Proposed** |
| Move, disambiguated by color | `Fusion Move Shape=rectangle FromX=120 FromY=150 ToX=350 ToY=280 Color=rouge` | **Proposed** |

For `move`, the palette resolves the shape under `(FromX, FromY)` using its `isClicked()` method. If `Shape=any`, do not filter by shape. If several candidates remain, **reject as ambiguous** rather than moving one arbitrarily. A spoken `Color` may further restrict candidates. The destination is `(ToX, ToY)`.

**Do not emit the proposed `Color` suffix to the current palette:** its existing creation regex accepts exactly `Fusion Create=<shape> X=<x> Y=<y>` and would ignore a longer message.

### Color designation lookup (proposed extension)

When the user says *"de cette couleur"*, the fusion engine needs the color of an object at a clicked point:

```text
Fusion GetColor X=220 Y=160 RequestId=7
Palette ColorAt RequestId=7 Color=rouge
```

The palette can implement this by testing `isClicked()` and calling the provided `getColor()`. Valid results are `rouge`, `vert`, `bleu`, `none`, or `ambiguous`. `RequestId` associates asynchronous replies with the outstanding request. The fusion controller must wait for the reply before issuing `Fusion Create=... Color=...` and should fail safely when there is no unambiguous color reference. This exchange is not yet implemented.

## 7. Rules owned by the fusion engine

1. **No monomodal user operation.** A completed user-facing create/move must combine at least two distinct input modalities from `{speech, gesture, pointing}`. Manual `ivyprobe` commands are allowed for technical testing only.
2. **Shape:** derived from recognized speech or gesture. Supported shapes: circle, rectangle, triangle, diamond.
3. **Explicit color:** must originate in speech. Gesture and pointing alone may never choose a new named color. For *"this color"*, speech requests a color reference, and pointing selects the source object.
4. **Explicit position:** *"here"* must be complemented by a click, not a default coordinate. Position and color can be provided in either order.
5. **Create:** color and position are optional, but the operation must still be multimodal (e.g. speech `create` + gesture `circle`). Defaults cannot be used to bypass rule 1.
6. **Move:** requires a resolvable target and destination; use pointing to designate them. Speech or gesture supplies the action; speech can supply shape/color filters.
7. **Ambiguity / contradiction:** never silently choose among several matching objects, or between conflicting shapes/colors. Wait for clarification, provide feedback, or cancel.
8. **Timeout:** proposed `FUSION_WINDOW_S = 4.0` between first and last matching input; configurable and to be validated experimentally in the chronograms. Keep recent unmatched events to support pointing preceding speech. On expiration, cancel the incomplete operation and clear the pending context.
9. **Reset:** clear consumed events and pending selection/color query after success, explicit cancel, or timeout. Do not reuse old clicks for a new operation.
10. **Confidence:** retain the recognizers' confidence values. Recognition acceptance thresholds are a shared configurable design choice, not a requirement of the raw wire protocol.

## 8. Acceptance tests before integration

| ID | Events / input | Expected result |
| --- | --- | --- |
| T01 | Speech `create circle red here`, then click `(200,180)` | One red circle at clicked point (after color support exists) |
| T02 | Click `(200,180)`, then speech `create circle here` within window | One circle at clicked point (reverse order) |
| T03 | Speech `create`, then gesture `circle` | One circle at documented default position |
| T04 | Speech `create circle` only, no other modality | **No creation**; incomplete/timeout |
| T05 | Gesture `circle` only | **No creation**; incomplete/timeout |
| T06 | Speech `create circle this color`, click on a red shape | Query color then create a red circle, if shape location uses a default; two modalities |
| T07 | Speech/gesture `move`, click source then destination | Correct shape moves |
| T08 | Move target overlaps two matching shapes, no disambiguating color | No arbitrary move; ambiguity feedback |
| T09 | Move matching shape with speech color filter | Only the matching colored shape moves |
| T10 | Too much delay between required events | Operation expires; nothing created/moved |
| T11 | Two successive complete operations | No leaked selection or color between them |

Tests T01–T11 describe intended future behavior, **not a statement of current implementation**.

## 9. Implementation handoff and merge order

1. **Together:** approve canonical vocabulary, `InputEvent`, `PaletteCommand`, and the temporal scenarios; add this document and `fusion_engine/events.py` to `main`.
2. **Developer A / `feature/modalities`:** implement raw Ivy parsing and `on_event()` delivery; emit `Palette Click` and extend command handlers in Processing; create controlled input simulators.
3. **Developer B / `feature/fusion-engine`:** implement controller, buffer, FSM, timeout and deterministic tests by creating `InputEvent` instances directly.
4. **Together:** integration tests with the real palette and gesture/speech agents; document the message traces, FSM, chronograms and screenshots.

Every interface change needs an updated contract and a corresponding integration test. Keep existing `Fusion Create=<shape> X=<x> Y=<y>` working during the transition.
