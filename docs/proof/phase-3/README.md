# Bằng chứng Phase 3

Lệnh chạy lại từ gốc repo. `run-a.jsonl` và `run-b.jsonl` do chương trình ghi, cùng seed 1, và giống nhau từng byte.

```bash
python -m pytest -q
python -m lantern headless --seed 1 --night 1 --ticks 60 --scenario docs/proof/phase-3/scenario.json --inputs docs/proof/phase-3/inputs.json --out docs/proof/phase-3/run-a.jsonl
```

`pytest.txt` là output thật của pytest. Scenario này để một Bóng Mực hút đèn dầu 29 trong 60 tick. File kết quả phải có `fuel_drain` và đèn còn sáng với dầu 23.0. Không sửa file JSONL cho khớp test.
