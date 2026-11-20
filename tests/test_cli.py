"""Headless command exit codes and deterministic files."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cli(tmp_path, extra, scenario=None, inputs=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    out = tmp_path / "out.jsonl"
    args = [
        sys.executable,
        "-m",
        "lantern",
        "headless",
        "--seed",
        "3",
        "--night",
        "1",
        "--ticks",
        "30",
        "--out",
        str(out),
        *extra,
    ]
    if scenario is not None:
        path = tmp_path / "scenario.json"
        path.write_text(json.dumps(scenario), encoding="utf-8")
        args.extend(["--scenario", str(path)])
    if inputs is not None:
        path = tmp_path / "inputs.json"
        path.write_text(inputs if isinstance(inputs, str) else json.dumps(inputs), encoding="utf-8")
        args.extend(["--inputs", str(path)])
    completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return completed, out


def test_two_runs_match_bytes(tmp_path):
    scenario = {"random_motes": False, "random_shades": False, "motes": [[0, 0, 4]], "shades": []}
    inputs = {"frames": [{"tick": 0, "move": [0, 1]}]}
    first, path_a = run_cli(tmp_path / "a", [], scenario, inputs)
    second, path_b = run_cli(tmp_path / "b", [], scenario, inputs)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert path_a.read_bytes() == path_b.read_bytes()
    lines = [json.loads(line) for line in path_a.read_text(encoding="utf-8").splitlines()]
    assert lines[0]["type"] == "snapshot"
    assert lines[-1]["type"] == "end"
    assert "\r" not in path_a.read_text(encoding="utf-8")


def test_bad_json_exits_2(tmp_path):
    completed, _out = run_cli(tmp_path, [], inputs="{")
    assert completed.returncode == 2
    assert completed.stderr.strip()


def test_missing_file_exits_1(tmp_path):
    out = tmp_path / "out.jsonl"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "lantern",
            "headless",
            "--seed",
            "1",
            "--night",
            "1",
            "--ticks",
            "1",
            "--scenario",
            str(tmp_path / "missing.json"),
            "--out",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1


def test_wrong_night_exits_1(tmp_path):
    out = tmp_path / "out.jsonl"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "lantern",
            "headless",
            "--seed",
            "1",
            "--night",
            "2",
            "--ticks",
            "1",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
