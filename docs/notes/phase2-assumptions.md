# Giả định Phase 2

Ticket-02 thay mọi số Phase 1. Các số khai trong `game.contract.json` là số chuẩn. Chỗ ticket không khóa từng tick được ghi ở đây.

## Số và điểm

- Tăng tốc tới 6 m/s ngay trong bước đầu. 0 giây vẫn nằm trong giới hạn 0,1 giây, nên 60 tick đi thẳng đúng bằng 6 mét như bài test Phase 1.
- `+10` cộng khi nạp đom đóm vào đèn, không cộng khi nhặt.
- `hit_drop_ratio` = 0,5 được tính bằng `floor(đang mang / 2)`.
- `shade_speed` trong contract là 4,0. Đêm 3 dùng 4,5 chỉ trong code.
- Nhảy 7 m/s và trọng lực −20 không có khóa riêng trong contract, vì danh sách khóa v1.1 không thêm hai mục đó.

## Bóng Mực

- Không ghi `state` thì mặc định `chase`, để kịch bản Phase 1 vẫn thấy Bóng Mực đuổi ngay.
- `wander` đứng yên. Vào `chase` khi cách ≤ 12 m. Thoát `chase` khi cách > 18 m.
- Tâm = chân + 1 m. Chân đi trên mặt đảo, bước lên dốc nếu cao hơn không quá 0,25 m. Không leo vách.
- Đêm 2: 1 con tại tick 420, 840, … tối đa 8. Đêm 3: 1 con tại tick 360, 720, … tối đa 10.
- Một đợt sinh bị bỏ nếu không đủ điểm cách người chơi ≥ 15 m.
- Bị Tỏa Sáng: choáng 120 tick, 15 tick đầu bị đẩy tổng 4 m. Đẩy dừng ở mép đảo.
- Đèn vừa sáng: Bóng Mực đang ở trong vòng 6 m bị đẩy ra mép trong 30 tick và không đánh trong lúc đó.

## Đêm, gió, bùa, Gió Lạc

- 20 đom đóm đầu là 20 điểm đầu trong danh sách bản đồ. Điểm sau tick 240, 480, … được chọn trong các điểm còn trống.
- Đom đóm của bản đồ có `ttl_s` null. Đom đóm rơi sống 480 tick, nhặt được từ tick sau, và nằm trên vành 1,5–2,5 m.
- Gió Lạc thả đồ tại chỗ nó đang bay. Điểm sương: Đêm 2 là 8 điểm bán kính 16 m mỗi đảo; Đêm 3 là 12 điểm bán kính 28 m.
- Gió Đêm 3: báo trước từ tick 1680, thổi từ tick 1800 trong 300 tick, rồi lặp mỗi 1800 tick. Hướng lấy từ seed. Đêm 1 và 2 tắt gió trừ khi scenario bật.
- `night_start` ghi ở bước chơi đầu tiên. Dừng ngay từ tick 0 thì không có event và không cộng điểm.
- `invuln`, `dash_cd_s`, `pulse_cd_s`, `charm_s` trong snapshot là số giây còn lại.
- Tạm dừng là cạnh lên của `pause`. Vừa tạm dừng thì bỏ phần còn lại của bước. Bấm lại thì tiếp tục ngay trong bước đó.
- Rơi: chờ đúng 60 tick rồi hồi sinh ở (0, 0, 0). Hết Ngọn Lửa thì thua, không hồi sinh.
- Điểm headless là điểm của một Đêm. Tổng ba Đêm chỉ cộng ở màn hình Bình Minh.
