# Bằng chứng Phase 1

Lệnh chạy lại từ gốc repo. Hai file `run-a.jsonl` và `run-b.jsonl` được ghi bởi chương trình, cùng seed 1, và giống nhau từng byte.

```bash
python -m pytest -q
python -m lantern headless --seed 1 --night 1 --ticks 120 --scenario docs/proof/phase-1/scenario.json --inputs docs/proof/phase-1/inputs.json --out docs/proof/phase-1/run-a.jsonl
```

`pytest.txt` là output thật của lần chạy 22 test, ngày làm bài.

Scenario này chứng minh:

- Tick 0 đứng ở gốc, trước khi áp input.
- Tick 25: `mote_picked`, đang mang 2.
- Tick 41: `pulse`, `stunned_ids` là `S1`.
- Tick 51: `deposit` vào `L1`.
- Dòng `end`: 120 tick, còn đang chơi, điểm 25 (10 điểm nhặt + 15 điểm choáng).

Các luật còn lại (đúng 6 mét sau 1 giây, vòng an toàn, bất tử, thắng, thua, bình minh, JSON hỏng thoát mã 2) nằm trong `tests/test_sim.py` và `tests/test_cli.py`.
