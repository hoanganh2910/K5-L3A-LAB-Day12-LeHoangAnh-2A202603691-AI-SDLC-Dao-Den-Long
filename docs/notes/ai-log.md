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
