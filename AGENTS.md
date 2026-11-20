# Đảo Đèn Lồng

Luật nằm trong `lantern/tuning.py` và bản đồ trong `lantern/world.py`. `game.contract.json` phải khớp `contract_dict()`. Đừng sửa output JSONL cho khớp test.

## Lệnh

- Chơi: `python -m lantern play`
- Headless: `python -m lantern headless --seed 1 --night 1 --ticks 300 --out out.jsonl`
- Test: `python -m pytest`

`--night` nhận 1, 2 hoặc 3. Headless không được import Ursina. View chỉ đọc trạng thái sim.

## Tick

60 tick mỗi giây. Snapshot tick 0 là sau khi dựng scenario, trước input. Bước k đọc input tick k và ra trạng thái sau bước đó. Event ghi tick của bước vừa chạy. `tick` vẫn tăng khi tạm dừng. `sim_tick` chỉ tăng khi game đang chạy.

Trong một bước đang chơi: giảm bộ đếm, di chuyển rồi xét rơi, nhặt, nạp đèn, vùng an toàn, tỏa sáng, di chuyển Bóng Mực và Gió Lạc, chạm, sinh theo lịch, rồi mới xét thắng thua. Ưu tiên kết thúc: hết Ngọn Lửa, thắp hết đèn, hết giờ.

Khoảng cách trên mặt phẳng XZ, trừ Tỏa Sáng dùng khoảng cách 3D. `<=` bán kính là trong tầm. Rơi khi Y < -10.
