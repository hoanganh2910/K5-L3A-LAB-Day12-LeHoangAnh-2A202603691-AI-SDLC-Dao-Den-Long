# Đảo Đèn Lồng

Ba đêm: Đảo Bến, Đảo Cau, Đảo Chuông. Mây nhặt đom đóm, thắp đèn, né Bóng Mực và Gió Lạc.

Video demo sẽ gắn ở đây khi có bản phát hành.

## Cài và chơi

Trên macOS hoặc Linux, trong thư mục repo:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m lantern play
```

Trên Windows, dùng `python` thay cho `python3` và `.venv\Scripts\activate`. Headless không cần cửa sổ hay GPU. Logic game là Python thuần, nên máy chấm không cần cài Ursina nếu chỉ chạy test ẩn; lệnh `build_cmd` trong `game.contract.json` vẫn cài đủ thư viện để mở game.

## Điều khiển

- WASD hoặc phím mũi tên: đi. Hướng phụ thuộc camera.
- Chuột: xoay camera.
- Space: nhảy khi đang chạm đất.
- Shift trái: lướt.
- E: nạp đom đóm vào đèn gần nhất còn nhận dầu (chưa sáng, hoặc sáng nhưng chưa đầy).
- F: tỏa sáng, tốn 3 đom đóm.
- Esc hoặc P: tạm dừng. Trong menu tạm dừng, phím 1 đến 4 chọn tiếp tục, chơi lại, cài đặt, về menu.
- Enter: bắt đầu, vào đêm, hoặc sang đêm sau.

## Cách tính điểm

- Mỗi đom đóm nạp vào đèn: 5.
- Thắp lần đầu: 100. Thắp lại: 40.
- Bóng Mực trúng Tỏa Sáng: 5, hoặc 15 nếu ngay trước đó nó đang hút dầu.
- Chỉ khi thắng lúc bình minh: mỗi đèn đang sáng được `50 + floor(dầu)`, và 50 điểm cho mỗi Ngọn Lửa còn lại. Không còn thưởng thời gian.

Tổng điểm ở màn Bình Minh là tổng điểm các đêm đã thắng. Đèn đặt sẵn sáng trong scenario headless không được điểm.

## Luật Đêm

Ngọn Lửa bắt đầu bằng 3 và hồi đầy đầu mỗi đêm. Túi bắt đầu mang được 10, tăng 2 sau mỗi lần thắp thành công, tối đa 20. Đèn mới cần 10 đom đóm, đèn đã từng sáng chỉ cần 5. Đèn đang sáng hao 1 dầu mỗi giây và có thể tắt. Đêm 1, 2, 3 dài 240, 270 và 300 giây. Hết Ngọn Lửa thì thua ngay. Hết giờ mà còn sống và đủ đèn đang sáng (Đêm 1 cần 3/5) thì thắng. Hết giờ mà thiếu đèn thì thua. Rơi khỏi đảo khi Y < −10.

Các số này nằm trong [game.contract.json](game.contract.json) và [lantern/tuning.py](lantern/tuning.py). Quyết định Phase 3: [docs/notes/adr-0001-lantern-fuel.md](docs/notes/adr-0001-lantern-fuel.md). Thay đổi phá vỡ tương thích: [CHANGELOG.md](CHANGELOG.md).

## Headless và test

```bash
python3 -m lantern headless --seed 1 --night 1 --ticks 300 --out out.jsonl
python3 -m pytest
```

`--night` nhận 1, 2 hoặc 3. Có thể thêm `--scenario tinh_huong.json --inputs phim.json --snapshot-every 10`. Cùng seed, cùng scenario và cùng inputs thì file kết quả giống nhau từng byte. JSON sai định dạng thì lệnh thoát với mã 2.

## Sáng tạo của tôi

Chỉ ở phần nhìn, không đổi file headless:

- Ba đảo vẽ theo bản đồ chuẩn: biển mây, cầu tre, tầng, dốc, tháp chuông và bục nhảy.
- Mây áo kem, khăn đỏ, nón lá. Đèn, đom đóm, Bóng Mực và Gió Lạc dùng bảng màu của ticket.
- Phần nhìn không ghi thêm gì vào file headless.

Bằng chứng phần lõi: `python3 -m pytest`, kết quả lưu trong [docs/proof/phase-3](docs/proof/phase-3). Bản Phase 1 vẫn nằm ở tag `phase-1`.

## Tài liệu lab

[GUIDE.md](GUIDE.md), [CHECKPOINTS.md](CHECKPOINTS.md), [SUBMISSION.md](SUBMISSION.md), [RULES.md](RULES.md), [RUBRIC.md](RUBRIC.md).
