# Tiêu chí chấp nhận Phase 2

Mỗi mục dưới đây có một scenario headless trong `tests/test_phase2.py`, trừ phần chỉ thuộc cửa sổ chơi.

## Gió Lạc

- Đêm 2 và 3, tối đa 2, id D1, D2, sinh tại tick 1200, 2400, … nếu còn chỗ.
- `idle` bay 2 m/s. Mang ≥ 5 và cách ≤ 15 m thì `chase` ở 7 m/s. Mất điều kiện thì về `idle`.
- Chạm XZ ≤ 1,2 m khi đang `chase`: cướp `min(3, đang mang)` một lần, rồi `flee` 240 tick và biến mất cùng số đã cướp.
- Tỏa Sáng trúng lúc `chase`: `flee` mà không cướp. Trúng lúc `flee` đang mang đồ: thả đúng số đó tại chỗ, biến mất sau 120 tick.
- Không trừ Ngọn Lửa. Vòng đèn và bất tử không chặn cú cướp.

## Bùa Gió

- Nhặt như đom đóm. Có hiệu lực 600 tick, nhặt lại thì làm mới. Hiện lại sau 2700 tick.
- Trong lúc có bùa: chạy 7,2 m/s, Lướt không hồi chiêu. Bấm khi đang lướt thì bỏ. Lướt vẫn 14 m/s trong 12 tick.
- Đêm 2 một bùa tại (35, 0, 0). Đêm 3 tại (30, 0, 25) và (−30, 0, 25).

## Lướt

- Hướng đang đi; đứng yên thì hướng đang quay mặt, mặc định +Z.
- 14 m/s trong 12 tick, hồi 90 tick kể từ lúc bắt đầu. Trên không không đổi độ cao. Không bất tử.
- Có event `dash`.

## Tạm dừng

- Esc hoặc P trên cửa sổ, và input `pause` khi headless.
- `tick` tăng, `sim_tick` đứng, thời gian và hồi chiêu đứng. Snapshot ghi `paused`.
- Menu: Tiếp tục, Chơi lại Đêm, Cài đặt, Về menu.

## Chuỗi ba Đêm

- Menu, giới thiệu, chơi, kết quả, Đêm sau. Thắng Đêm 3 thì Bình Minh với tổng điểm các Đêm đã thắng. Thua thì chơi lại đúng Đêm đó.
- Headless chơi một Đêm mỗi lần chạy.

## Cài đặt

- Âm lượng và độ nhạy chuột, lưu ở `~/.dao-den-long/settings.json`.

## Âm thanh

- Nhạc đêm lặp. Có tiếng cho nhặt, thắp đèn, tỏa sáng, bị đánh, nhảy, lướt, thắng, thua, Bóng Mực xuất hiện, và từng giây trong 10 giây cuối.
- Tiếng được tạo bằng sóng sin lúc chơi, không có file âm thanh trong repo.

## HUD

- Ngọn Lửa trên trái. Đồng hồ mm:ss trên giữa, đỏ và nhấp nháy khi còn ≤ 30 giây.
- Đèn k/n và điểm trên phải. Thanh 10 ô dưới giữa. Hồi Lướt và Tỏa Sáng dưới phải.
- Gần đèn chưa sáng: `E - Nap anh sang (x/10)`. Ngoài màn hình thì có dấu `>` chỉ hướng.

## Màu và ánh sáng

- Các phần được liệt kê trong ticket dùng đúng mã hex của bảng màu.
- Cường độ đèn môi trường = 0,15 + 0,55 × (đèn sáng / tổng đèn).

## Hiệu năng

- Một Đêm headless 21600 tick xong trong dưới 30 giây: `tests/test_phase2.py`.
- Cửa sổ 1280×720, đo 180 khung hình, ghi trong `docs/proof/phase-2/fps.txt`.
