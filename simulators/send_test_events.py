"""Send test Ivy messages, without sra5/OneDollarIvy/Processing.

Examples:
    python -m simulators.send_test_events speech --shape circle --color red --here
    python -m simulators.send_test_events gesture cercle
    python -m simulators.send_test_events click 200 180
"""

import argparse
import time

from ivy.std_api import IvyInit, IvySendMsg, IvyStart, IvyStop

BUS = "127.255.255.255:2010"


def main() -> None:
    parser = argparse.ArgumentParser(description="Send synthetic input over Ivy")
    sub = parser.add_subparsers(dest="modality", required=True)

    speech = sub.add_parser("speech")
    speech.add_argument("--action", choices=["create", "move"], default="create")
    speech.add_argument("--shape", choices=["circle", "rectangle", "triangle", "diamond"])
    speech.add_argument("--color", choices=["red", "green", "blue"])
    speech.add_argument("--here", action="store_true", help="Speech refers to a point")
    speech.add_argument("--confidence", type=float, default=0.95)

    gesture = sub.add_parser("gesture")
    gesture.add_argument("template", help="E.g. Cercle or rectangle")
    gesture.add_argument("--confidence", type=float, default=0.95)

    click = sub.add_parser("click")
    click.add_argument("x", type=int)
    click.add_argument("y", type=int)

    args = parser.parse_args()
    if args.modality == "speech":
        semantics = [f"action={args.action}"]
        if args.shape:
            semantics.append(f"shape={args.shape}")
        if args.color:
            semantics.append(f"color={args.color}")
        if args.here:
            semantics.append("position_ref=true")
        msg = (
            f"sra5 Parsed={' '.join(semantics)} "
            f"Confidence={args.confidence:.2f} NP=0 Num_A=0"
        )
    elif args.modality == "gesture":
        msg = f"OneDollarIvy Template={args.template} Confidence={args.confidence:.2f}"
    else:
        if args.x < 0 or args.y < 0:
            parser.error("click coordinates must be non-negative")
        msg = f"Palette Click X={args.x} Y={args.y}"

    IvyInit("InputSimulator", "InputSimulator Ready")
    IvyStart(BUS)
    try:
        # Allow the Ivy peer handshake to complete before sending.
        time.sleep(1.0)
        IvySendMsg(msg)
        print(f"[SENT] {msg}")
        time.sleep(0.5)
    finally:
        IvyStop()


if __name__ == "__main__":
    main()
