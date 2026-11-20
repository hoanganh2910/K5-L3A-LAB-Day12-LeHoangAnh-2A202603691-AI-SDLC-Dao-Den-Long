"""Headless CLI for Test Contract v1.1."""

from __future__ import annotations

import argparse
import json
import sys

from lantern.sim import FormatError, parse_inputs, run_simulation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lantern headless")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--night", type=int, required=True)
    parser.add_argument("--scenario", type=str)
    parser.add_argument("--inputs", type=str)
    parser.add_argument("--ticks", type=int, required=True)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--snapshot-every", type=int, default=10)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 1
    if args.night not in (1, 2, 3):
        print("night must be 1, 2, or 3", file=sys.stderr)
        return 1
    if args.ticks < 0 or args.snapshot_every < 1:
        print("ticks must be >= 0 and snapshot-every must be >= 1", file=sys.stderr)
        return 2
    try:
        scenario = _load_json(args.scenario) if args.scenario else None
        inputs = _load_json(args.inputs) if args.inputs else None
        frames = parse_inputs(inputs)
        lines = run_simulation(args.seed, scenario, frames, args.ticks, args.snapshot_every, args.night)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except FormatError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except json.JSONDecodeError:
        print("invalid json", file=sys.stderr)
        return 2
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    try:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            for line in lines:
                handle.write(json.dumps(line, ensure_ascii=False, separators=(", ", ": ")))
                handle.write("\n")
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _load_json(path: str) -> object:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"file not found: {path}") from exc


if __name__ == "__main__":
    sys.exit(main())
