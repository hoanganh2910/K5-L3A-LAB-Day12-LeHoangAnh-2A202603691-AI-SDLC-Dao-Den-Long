# Giả định Phase 1

PRD-0 không cho số. Các số dưới đây là luật đang chạy, và là các số khai trong `game.contract.json`.

## Số

- Mây 6 m/s, nhảy 6.5 m/s, trọng lực 20 m/s² hướng xuống. Nhảy không có trong contract.
- Túi 8. Nhặt trong 1.5 m. Một bước nhặt mọi đom đóm trong tầm, theo thứ tự id, cho đến khi đầy túi.
- Mỗi đèn 3 đom đóm. Nạp khi bấm tương tác trong 2 m. Một lần bấm nạp `min(đang mang, phần còn thiếu)` vào đèn chưa đầy gần nhất. Hòa khoảng cách thì chọn id nhỏ hơn.
- Tỏa sáng tốn 1 đom đóm đang mang, không tốn máu. Tầm 8 m. Đẩy 4 m ra xa. Choáng 1.5 giây. Hồi 0.8 giây.
- Máu 3. Chạm trừ 1, không rơi đom đóm (`hit_drop_ratio` = 0). Bất tử 1 giây.
- Bóng Mực 3.5 m/s, tầm chạm 1.2 m. Tâm ghi ở Y = 1. Chỉ con đang `chase` mới gây sát thương.
- Vòng an toàn 6 m chỉ quanh đèn đã thắp.
- Đêm 180 giây. Scenario có `time_left_s` thì dùng số đó.
- Điểm: nhặt 10, thắp đèn 100, mỗi con bị choáng 15. Thưởng `floor(giây còn lại)` và `20 * máu` chỉ khi thắng.
- `fall_enabled` = false. Sim là mặt phẳng XZ vô hạn. Đảo bán kính 40 m chỉ là hình, để quãng đường headless vẫn bằng tốc độ nhân thời gian.

## Thời gian đếm bằng tick

1 giây = 60 tick. Hồi chiêu, choáng và bất tử dùng số tick nguyên để khỏi lệch số thực.

- Hồi tỏa sáng: 48 tick. Bấm ở tick k thì bấm lại được ở tick k+48.
- Choáng: 90 tick không đuổi, tính cả tick vừa tỏa sáng. Tick k+90 thì đuổi tiếp.
- Bất tử: bị chạm ở tick k thì cú chạm sau sớm nhất là tick k+60.

## Thứ tự trong một tick

1. Giảm hồi chiêu và bất tử.
2. Di chuyển theo công thức contract, rồi nhảy.
3. Nhặt đom đóm.
4. Tỏa sáng, nếu hết hồi và còn đủ đom đóm.
5. Nạp đèn.
6. Sinh Bóng Mực nếu đến lịch, rồi choáng hoặc đuổi.
7. Chạm, tối đa một cú, id nhỏ trước.
8. Hết máu thì thua. Không thì đủ đèn thì thắng và cộng thưởng. Không thì hết giờ thì thua vì bình minh.

Dựng scenario không phát event và không cộng điểm. Đèn đặt `lit: true` sẵn không được 100 điểm. Nếu ngay từ đầu đã hết máu, đã thắp hết đèn, hoặc `time_left_s` bằng 0, game dừng ở tick 0 và không chạy thêm bước.

## Màn chơi thường

15 đom đóm đặt tay, đúng bằng 5 đèn nhân 3. Hai Bóng Mực có sẵn. Khi `random_shades` là true, cứ 20 giây sinh thêm một con trên vòng bán kính 28 m nếu đang ít hơn 4, vị trí lấy từ seed. `random_motes: false` và không liệt kê thì không có đom đóm. Danh sách trong scenario thay danh sách mặc định.

Id tự gán: đom đóm `M1`, `M2`, ... theo thứ tự mảng. Bóng Mực `S1`, `S2`, ... trừ khi scenario ghi id.
