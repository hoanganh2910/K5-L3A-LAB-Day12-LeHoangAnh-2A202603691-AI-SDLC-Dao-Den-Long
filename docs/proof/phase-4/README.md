# Bằng chứng Phase 4

Số trong `bench.json` và `soak.json` là kết quả chạy thật trên máy làm bài, không phải ngưỡng của máy chấm.

```bash
python -m pytest -q
python -m lantern soak --seed 7 --nights 10 --out docs/proof/phase-4/soak.json
python -m lantern bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json
```

Soak: 10 đêm, 0 crash, bộ nhớ đầu và cuối bằng nhau, dưới ngưỡng 1.2 lần.

Bench mở cửa sổ 1280×720, vsync tắt bằng `sync-video false`. Ba giây đầu không tính. File ghi lại FPS trung bình, 1% khung chậm, phân vị 95, số khung, thời gian tải và RSS. Máy này không phải máy chấm; ngưỡng 60 FPS áp vào máy giảng viên.
