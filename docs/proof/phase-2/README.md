# Bằng chứng Phase 2

Lệnh chạy lại từ gốc repo. `run-a.jsonl` và `run-b.jsonl` do chương trình ghi, cùng seed 1, và giống nhau từng byte.

```bash
python -m pytest -q
python -m lantern headless --seed 1 --night 1 --ticks 120 --scenario docs/proof/phase-2/scenario.json --inputs docs/proof/phase-2/inputs.json --out docs/proof/phase-2/run-a.jsonl
```

`pytest.txt` là output thật: 33 test, gồm hồi quy số chuẩn và một scenario cho mỗi tính năng mới.

File headless của scenario này có:

- Tick 1: `night_start` và `mote_picked`, đang mang 5.
- Tick 21: `pulse`, `stunned_ids` là `S1`.
- Tick 22: `dash`.
- Dòng `end`: 120 tick, còn đang chơi.

Đêm đủ 21600 tick và các luật còn lại nằm trong `tests/test_sim.py` và `tests/test_phase2.py`.
