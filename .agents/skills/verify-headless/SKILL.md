---
name: verify-headless
description: Run the Night 1 headless contract and save the real pytest output under docs/proof. Use after a sim change, before calling a phase done.
---

# Verify headless

1. Run `python -m pytest -q` from the repo root. Paste the terminal output into `docs/proof/phase-1/pytest.txt`. Do not edit the output.
2. Run one scenario twice:

```bash
python -m lantern headless --seed 1 --night 1 --ticks 120 --scenario docs/proof/phase-1/scenario.json --inputs docs/proof/phase-1/inputs.json --out docs/proof/phase-1/run-a.jsonl
python -m lantern headless --seed 1 --night 1 --ticks 120 --scenario docs/proof/phase-1/scenario.json --inputs docs/proof/phase-1/inputs.json --out docs/proof/phase-1/run-b.jsonl
```

3. Compare the two files. They must be identical. If a test fails, fix the sim or the assumption note. Do not hand-edit a JSONL result.
