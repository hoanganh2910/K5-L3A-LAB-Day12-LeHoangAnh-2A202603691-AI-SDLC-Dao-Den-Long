# Đảo Đèn Lồng

Night 1 chỉ có một luật, nằm trong `lantern/tuning.py`. `game.contract.json` phải khớp file đó. Đừng sửa output JSONL cho khớp test.

## Lệnh

- Chơi: `python -m lantern play`
- Headless: `python -m lantern headless --seed 1 --night 1 --ticks 300 --out out.jsonl`
- Test: `python -m pytest`

Headless không được import Ursina. View chỉ đọc trạng thái sim.

## Tick

60 tick mỗi giây. Snapshot tick 0 là sau khi dựng scenario, trước input. Bước k đọc input tick k và ra trạng thái k+1. Event ghi tick k+1.

Trong một bước: giảm hồi chiêu và bất tử, di chuyển, nhặt, tỏa sáng, nạp đèn, cập nhật Bóng Mực, chạm, rồi mới xét thắng thua. Ưu tiên kết thúc: hết máu, thắp hết đèn, hết giờ.

Khoảng cách chỉ tính trên XZ. `<=` bán kính là trong tầm. Không có tường đảo trong sim. `fall_enabled` là false.
