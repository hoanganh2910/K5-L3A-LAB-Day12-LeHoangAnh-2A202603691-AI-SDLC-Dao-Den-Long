# Retro bốn phase

## Phase 1

Làm được một đêm chơi và headless đúng hợp đồng. Việc hiệu quả là chốt thứ tự tick và một nguồn số trước khi viết sim. Việc không hiệu quả là đoán màu Ursina: `color.rgb` nhận 0–1 nên cả màn hình trắng, kể cả sương. Test bắt lỗi nạp đom đóm: một lần bấm nạp hết phần còn thiếu, không phải từng con.

## Phase 2

Ba đêm, lướt, bùa, gió, tạm dừng. AI viết đúng khung, nhưng lần bấm lướt khi còn hồi chiêu nuốt cạnh nút, nên test phải tách lần bấm bị chặn và lần bấm khi đã hồi. Thắp đèn cuối cùng làm đêm thắng ngay, nên bài đẩy Bóng Mực không được để sẵn các đèn kia sáng. Cửa sổ offscreen không khóa được chuột.

## Phase 3

Đổi mục tiêu từ thắp hết sang giữ sáng tới bình minh. Quyết định dầu bằng số nguyên 1/60 tránh sai số. AI suýt tính châm dầu trên số dầu đầu tick; luật là trừ dầu trước rồi mới tương tác. Dòng `end` luôn được ghi khi chạy hết số tick, kể cả khi còn đang chơi. Test cũ bị luật mới làm sai được sửa và ghi trong changelog, không skip.

## Phase 4

Thêm đo, soak, bảng xếp hạng và phím. Luật headless không đổi. Soak 10 đêm trên máy này hết khoảng 2 giây, 0 crash, bộ nhớ không tăng. Benchmark trên máy này thấp hơn ngưỡng 60 FPS của máy chấm; file `bench.json` là số đo thật, không phải số cần đạt.

## Làm với AI

Hiệu quả khi có hợp đồng, test headless, và một file số. Không hiệu quả khi nhờ AI đoán đồ họa hoặc sửa file JSONL cho khớp test. Những lần AI sai đều lộ ra vì pytest hoặc vì hai lần headless không giống nhau. Không có lần nào sửa output cho đẹp.

Harness giúp nhiều nhất là `AGENTS.md` (thứ tự tick, cấm import Ursina ở headless, cấm sửa JSONL) và skill `verify-headless`. Không có hook tự động nào trong repo.

Cursor không hiện token. Mình không ước một con số cho có. Chi phí là gói Cursor, không có hóa đơn theo token để ghi. Cách đỡ tốn lượt: chốt luật trước, một nguồn số, test trước cửa sổ, không mở vòng lặp agent trên đồ họa khi test chưa xanh.

Nếu làm lại, mình gắn tag từng phase ngay khi test xanh, không để phase 2 và 3 nằm local rồi mới commit. Video demo phải quay trong lúc cửa sổ còn mở, không để đến phút cuối.

## Chỗ chưa xong

Chưa có file `demo.mp4`. Mình không tạo video giả. Ảnh `images/night1.png` là ảnh thật từ cửa sổ benchmark.
