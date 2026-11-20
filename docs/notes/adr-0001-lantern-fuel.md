# ADR 0001 — Đèn có dầu, thắng lúc bình minh

Trạng thái: đã chọn cho Phase 3, Contract v1.2.

## Bối cảnh

Phase 2 kết thúc Đêm ngay khi mọi đèn sáng. Playtest cho thấy người chơi giỏi xong việc quá sớm. Ticket-03 đổi mục tiêu thành giữ đảo sáng tới bình minh, và cho Bóng Mực hút dầu đèn yếu.

## Trạng thái đèn

Một đèn có `lit`, `deposited`, `fuel`, `ever_lit`, `relit_count`.

- Chưa từng sáng: cần 10 đom đóm. Khi đủ, `lit`, `fuel = 100`, `ever_lit = true`, `relight: false`.
- Đang sáng: mỗi tick trừ 1/60 dầu, cộng thêm 5/60 cho mỗi Bóng Mực đang `drain` đèn đó. `fuel <= 0` thì tắt ngay trong bước đó, `deposited = 0`, phát `lantern_out`, giữ `ever_lit`.
- Đã từng sáng mà đang tắt: thắp lại bằng 5 đom đóm, `relit_count` tăng 1, `relight: true`.
- Đang sáng nhưng chưa đầy: bấm tương tác châm dầu. `used = 0` thì đèn không được chọn.

Dầu lưu bằng số nguyên 1/60. 100 dầu là 6000 đơn vị. Chỉ làm tròn 1 chữ số thập phân khi ghi snapshot và event. Cách này tránh cộng dồn sai số số thực qua hàng nghìn tick.

Đèn đặt sẵn `lit: true` mà không ghi `fuel` được 100 dầu và `ever_lit`, nhưng không tính là một lần thắp và không cộng điểm. Nếu scenario đã hết giờ ngay lúc dựng, sim chỉ đặt thắng hoặc thua theo ngưỡng, không phát event và không cộng điểm bình minh. Điểm bình minh chỉ cộng khi tick chơi thật sự chạm hết giờ.

## Luật thắng

Không còn `all_lit`. Cuối tick, hết Ngọn Lửa luôn ra `no_flames` trước. Nếu tick đó cũng là bình minh và Mây còn sống, thắng `dawn_survived` khi số đèn đang sáng >= ceil(0.6 × tổng đèn). Thiếu đèn thì thua `dawn`.

## Bóng Mực

`wander` chọn đèn sáng có dầu dưới 30 gần nhất. Không có thì đi tới đèn tắt gần nhất. Phase 2 từng để `wander` đứng yên; câu này trong Ticket-03 thay cách đó. `chase` không đổi mục tiêu. Trong 2 m của đèn yếu thì sang `drain`, đứng yên và hút. Hết choáng thì về `wander`.

Đèn dầu dưới 30 không còn vùng an toàn. Đúng 30 vẫn còn. Châm dầu lên từ dưới 30 thì Bóng Mực đang trong 6 m bị đẩy ra mép, giống lúc đèn vừa thắp.

Tỏa Sáng trúng một con đang `drain` được 15 điểm tất cả, không phải 5 rồi thêm 15. Con không hút dầu vẫn được 5.

## Phần nhìn

Cài đặt "Bảng màu dễ phân biệt" lưu trong `~/.dao-den-long/settings.json`. Viền và mắt Bóng Mực dùng `#00B3FF`. Màu cảnh báo dùng trắng. Font mặc định không vẽ được ký tự ⚠, nên HUD dùng `( ! )` viết liền thành `(!)`. Đèn tắt xẹp 20% và có vết rách. Dầu dưới 30 thì đèn và thanh dầu nhấp 1 Hz. Những thứ này không ghi vào file headless.
