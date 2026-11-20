# Đảo Đèn Lồng

Đêm 1 – Đảo Bến. Mây nhặt đom đóm, thắp 5 Đèn Lồng Lớn, và né Bóng Mực.

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
- Chuột: xoay camera. Esc khóa hoặc mở chuột.
- Space: nhảy.
- E: nạp đom đóm đang mang vào đèn gần nhất chưa sáng.
- F: tỏa sáng, xua Bóng Mực, tốn 1 đom đóm.
- R: chơi lại sau khi thắng hoặc thua.

## Cách tính điểm

- Nhặt 1 đom đóm: 10.
- Thắp 1 đèn: 100.
- Mỗi Bóng Mực bị choáng: 15.
- Chỉ khi thắng: thêm số giây còn lại (làm tròn xuống) và 20 điểm cho mỗi máu còn lại.

Thua không được thưởng thời gian hay máu. Đèn đặt sẵn sáng trong scenario headless không được điểm.

## Luật Đêm 1

Máu bắt đầu bằng 3. Túi mang tối đa 8 đom đóm. Mỗi đèn cần 3 đom đóm. Chạm Bóng Mực mất 1 máu và bất tử 1 giây, không làm rơi đom đóm. Tỏa sáng tầm 8 mét, choáng 1,5 giây, đẩy ra 4 mét, hồi 0,8 giây. Đèn đã thắp có vòng an toàn 6 mét. Đêm dài 180 giây. Hết máu thì thua. Hết giờ thì bình minh và thua. Thắp hết 5 đèn thì thắng.

Các số này nằm trong [game.contract.json](game.contract.json) và [lantern/tuning.py](lantern/tuning.py). Giả định cho chỗ PRD không nói rõ: [docs/notes/phase1-assumptions.md](docs/notes/phase1-assumptions.md).

## Headless và test

```bash
python3 -m lantern headless --seed 1 --night 1 --ticks 300 --out out.jsonl
python3 -m pytest
```

Có thể thêm `--scenario tinh_huong.json --inputs phim.json --snapshot-every 10`. Cùng seed, cùng scenario và cùng inputs thì file kết quả giống nhau từng byte. JSON sai định dạng thì lệnh thoát với mã 2.

## Sáng tạo của tôi

Chỉ ở phần nhìn, không đổi file headless:

- Đảo tròn có vân cỏ, biển quanh đảo, Mây có áo và nón lá, đèn và đom đóm có quầng sáng.
- Vũng sáng vàng dưới mỗi đèn đã thắp. Sương tím nhạt dần khi đảo sáng thêm đèn.
- Đom đóm nhấp nhô khi vẽ. Trong mô phỏng chúng vẫn là điểm trên mặt đất.

Bằng chứng phần lõi vẫn đúng: `python3 -m pytest`, kết quả lưu trong [docs/proof/phase-1](docs/proof/phase-1).

## Tài liệu lab

[GUIDE.md](GUIDE.md), [CHECKPOINTS.md](CHECKPOINTS.md), [SUBMISSION.md](SUBMISSION.md), [RULES.md](RULES.md), [RUBRIC.md](RUBRIC.md).
