# Giả định Phase 4

Những chỗ ticket không khóa một công thức, mình chốt như sau.

## Benchmark

- Cảnh dựng bằng `bench_scenario(seed)`. 200 Bóng Mực và 100 đom đóm rải theo hình xoắn ốc vàng, seed chỉ xoay cả hình. Bán kính tối đa 36 m và 18 m, nằm trong đảo Đêm 1.
- `Sim.bench` chỉ bật trong cảnh này. Mỗi tick chỉ chạy bước di chuyển Bóng Mực. Không hao dầu, không nhặt, không sát thương, không sinh thêm, không kết thúc Đêm. Mây không nhận input và đứng ở (0, 0, 0).
- Luật wander vẫn là luật thường: trong 12 m thì đuổi, không thì đi tới đèn yếu hoặc đèn tắt gần nhất. Ticket chỉ tắt sát thương, không tắt việc đổi trạng thái.
- Camera: góc 0 là (30, 15, 0). Ngược chiều kim đồng hồ khi nhìn từ trên xuống là chiều dương quanh trục Y, một vòng 15 giây.
- 3 giây đầu không ghi mẫu. `load_ms` tính từ lúc tiến trình bắt đầu tới khung đầu tiên sau khi cảnh đã dựng.
- `frame_ms_p95` lấy theo hạng gần nhất: vị trí `ceil(0.95 × N) − 1` trong danh sách dt đã sắp. `p1_low_fps` lấy `k = max(1, ceil(0.01 × N))` khung chậm nhất.
- Vsync tắt bằng cấu hình Panda3D `sync-video false` trước khi mở cửa sổ. `vsync_off` là giá trị đọc lại được. Nếu driver vẫn ép vsync, số FPS sẽ phản ánh điều đó.
- Không có kẻ địch sáng tạo ngoài Bóng Mực và Gió Lạc. Cảnh bench không có Gió Lạc, bùa, gió, hay sinh thêm.

## Soak

- Đêm thứ i, i bắt đầu từ 1. Seed là `seed + i`. Số Đêm trong game là `((i - 1) % 3) + 1`, nên 10 đêm đi 1, 2, 3, 1, 2, 3, 1, 2, 3, 1.
- Mỗi tick, nếu `tick % 30 == 0` thì random góc đi trước, rồi mới lần lượt xác suất nhảy, lướt, tỏa sáng, tương tác.
- `mem_start_mb` đo sau khi dựng xong Đêm đầu. `mem_end_mb` đo sau khi xong Đêm cuối và đã thu gom bộ nhớ. Đơn vị là RSS, MB.

## Bảng xếp hạng và phím

- Tên hợp lệ là 3–12 ký tự: chữ ASCII, số, `_`, hoặc chữ có dấu. Dấu cách và ký hiệu thì từ chối.
- `seed` lưu trong bảng là seed của đêm vừa kết thúc: `1 + số đêm`.
- Hòa điểm thì `achieved_at` sớm hơn đứng trên. Chuỗi ISO 8601 có múi giờ sắp được theo thời gian.
- Bốn hướng WASD đổi được. Phím mũi tên vẫn đi được, để không mất điều khiển cũ. Phím tắt tạm dừng `p` vẫn mở menu.
- Cỡ chữ nhỏ nhất trên HUD là scale 1. Với `Text.size` 0.025 của Ursina, đó là 18 px trên cửa sổ cao 720. Chữ lớn nhân 1.25.
- Giảm chuyển động tắt rung camera khi bị đánh, tắt nhấp camera lúc đi, và tắt chớp đỏ trên màn hình. Mũi tên và dòng chữ cảnh báo vẫn hiện.
