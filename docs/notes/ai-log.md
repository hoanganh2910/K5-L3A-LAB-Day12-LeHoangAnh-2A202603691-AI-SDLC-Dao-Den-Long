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

# Nhật ký dùng AI — Phase 3

Cùng công cụ Cursor. Giao diện vẫn không có bộ đếm token, nên không ghi số ước.

## Cách làm

- Giữ dầu bằng số nguyên 1/60 trong sim, chỉ làm tròn khi xuất snapshot và event. Ghi quyết định ở `docs/notes/adr-0001-lantern-fuel.md`.
- Sửa test cũ bị luật mới làm sai ngay trong file test, và ghi lý do trong `CHANGELOG.md`. Không dùng skip.
- Thêm `tests/test_phase3.py` cho hao dầu, châm dầu, thắp lại, sức chứa, hút dầu, vùng an toàn và bình minh.
- Phần nhìn thêm thanh dầu, đèn xẹp, và bảng màu dễ phân biệt. File headless không đổi vì những thứ đó.

## Lỗi đã bắt

- Một lần bấm châm dầu xảy ra sau bước trừ dầu, nên `ceil((100 − fuel) / 10)` phải tính trên dầu đã hao 1/60 của tick đó.
- Dòng `end` luôn được ghi khi chạy hết số tick, kể cả khi còn đang chơi. Test "không thắng sớm" phải nhìn `state`, không phải loại dòng cuối.

# Nhật ký dùng AI — Phase 4

Vẫn là Cursor, vẫn không có bộ đếm token. Không ghi số ước.

## Cách làm

- Tách công thức FPS, cảnh bench, soak và bảng xếp hạng ra module không import Ursina, rồi mới mở cửa sổ.
- `Sim.bench` là một nhánh tắt trong `step`. Headless thường không bật cờ này.
- Soak và pytest chạy trước. Cửa sổ benchmark chạy sau, và file json là số đo thật.

## Lỗi đã bắt

- Đọc RSS trên Windows bằng `psapi` trả về rỗng. Đổi sang `K32GetProcessMemoryInfo` thì đo được.
- Cửa sổ benchmark có lúc bị tắt giữa chừng nên file chưa kịp ghi. Lệnh đo ghi lại file theo từng mốc 5 giây để còn số khi tiến trình dừng.
