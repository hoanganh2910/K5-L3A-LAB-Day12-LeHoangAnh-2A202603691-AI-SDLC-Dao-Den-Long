# Nhật ký dùng AI — Phase 1

Công cụ: Cursor, agent trong repo này. Chưa có số token do giao diện không hiện bộ đếm. Không ước một con số cho có vẻ chính xác.

## Cách làm để đỡ tốn lượt

- Chốt số và thứ tự tick trong plan trước khi viết sim.
- Một nguồn số (`lantern/tuning.py`) sinh `game.contract.json`.
- Viết test headless trước cửa sổ 3D. Sửa test khi kỳ vọng sai luật, không sửa output.
- Không mở agent vòng lặp trên phần đồ họa khi test chưa xanh.

## Lỗi đã bắt trong lúc kiểm

- Kỳ vọng "mỗi lần bấm chỉ nạp 1 đom đóm" sai với luật đã chốt: một lần bấm nạp hết phần đèn còn thiếu. Test được sửa cho khớp luật.
- Lần tỏa sáng thứ hai không cộng điểm vì Bóng Mực đã bị đẩy ra ngoài tầm 8 m. Đó là luật tầm, không phải mất event.

# Nhật ký dùng AI — Phase 2

Cùng công cụ Cursor. Vẫn không có bộ đếm token trên giao diện, nên không ghi một con số ước cho có.

## Cách làm

- Giữ một nguồn số ở `lantern/tuning.py` và một nguồn bản đồ ở `lantern/world.py`.
- Viết lại sim theo thứ tự tick của Ticket-02 trước, chạy pytest, rồi mới làm cửa sổ.
- Test Phase 1 được sửa theo số chuẩn mới. Không sửa file JSONL cho khớp test.
- Đo FPS bằng `python -m lantern play --bench`, 180 khung ở 1280×720.

## Lỗi đã bắt

- Bấm lướt khi còn hồi chiêu nuốt mất cạnh nút, nên lần bấm sau không còn là cạnh lên. Test tách lần bấm bị chặn và lần bấm khi đã hồi.
- Thắp đèn cuối cùng làm đêm thắng ngay, nên bài test đẩy Bóng Mực ra khỏi vòng an toàn không được để sẵn các đèn kia sáng.
- Cửa sổ offscreen không khóa được chuột. Nhánh đo FPS bỏ qua bước đó.
