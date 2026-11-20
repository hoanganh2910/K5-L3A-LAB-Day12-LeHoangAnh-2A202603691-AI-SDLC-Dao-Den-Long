"""python -m lantern play | python -m lantern headless ..."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(
            "usage: python -m lantern play\n"
            "       python -m lantern headless --seed N --night 1|2|3 --ticks N --out FILE",
            file=sys.stderr,
        )
        return 0 if args and args[0] in ("-h", "--help") else 1
    command = args[0]
    if command == "headless":
        from lantern.headless import main as headless_main

        return headless_main(args[1:])
    if command == "play":
        from lantern.play import main as play_main

        return play_main(args[1:])
    print(f"unknown command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
