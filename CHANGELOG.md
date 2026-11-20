# Changelog

## Phase 4 — Contract v1.3

Không đổi luật Đêm. Thêm phát hành:

- `contract_version` là `1.3`. `game.contract.json` thêm `bench_cmd` và `soak_cmd`.
- `python -m lantern bench` đo cửa sổ 1280×720. `python -m lantern soak` chạy nhiều Đêm headless trong một tiến trình.
- Bảng xếp hạng cục bộ, xuất bằng `python -m lantern play --export-leaderboard`.
- Đổi phím, phụ đề, giảm chuyển động, chữ lớn. Lưu cùng cài đặt cũ.
- Test `test_contract_file_matches_tuning` đổi kỳ vọng phiên bản từ 1.2 sang 1.3 và kiểm tra hai lệnh mới. Số tuning không đổi. Không có test nào bị skip.

## Phase 3 — Contract v1.2

Phá vỡ tương thích với v1.1:

- `contract_version` là `1.2`. Đêm 1, 2, 3 còn 240, 270, 300 giây, không còn 300, 330, 360.
- Thắp hết đèn không còn thắng. `game_over.reason` bỏ `all_lit`. Thắng là `dawn_survived`. Thua hết giờ vẫn là `dawn`. Hết Ngọn Lửa vẫn là `no_flames` và được xét trước.
- Điểm mỗi đom đóm nạp vào đèn từ 10 xuống 5. Bỏ thưởng thời gian (`per_second_left` = 0). Thắp lại được 40. Bình minh chỉ cộng điểm khi thắng: mỗi đèn đang sáng `50 + floor(dầu)`, mỗi Ngọn Lửa còn lại 50.
- Snapshot đèn thêm `fuel`, `ever_lit`, `relit_count`. Người chơi thêm `capacity`. Bóng Mực thêm trạng thái `drain`.
- `lantern_lit` thêm `relight`. Event mới: `refuel`, `lantern_out`, `fuel_drain`.
- Tuning thêm `fuel_max`, `fuel_decay_per_s`, `fuel_per_mote`, `relight_cost`, `win_ratio`, `drain_per_s`, `low_fuel_threshold`, `capacity_max`.

Test được sửa, không bỏ qua:

- `test_contract_file_matches_tuning` đối chiếu số v1.2.
- `test_deposit_scores_and_lights_the_nearest_lantern` chờ 150 điểm và `relight: false`. Thắp một đèn không kết thúc đêm.
- `test_prelit_lanterns_do_not_score_or_emit_events` không còn chờ thắng ngay. Đèn đặt sẵn có dầu 100 và đêm vẫn đang chơi.
- `test_win_uses_the_standard_bonus` đổi thành `test_dawn_survived_replaces_the_early_all_lit_win`. Không còn thưởng `floor(giây còn lại) × 2`.

## Phase 1 — Contract v1.0

Đêm 1 chơi được và có headless. Tag `phase-1`.

## Phase 2 — Contract v1.1

Ba đêm, số chuẩn, lướt, bùa, Gió Lạc, gió và tạm dừng. Ghi ở tag và bằng chứng `docs/proof/phase-2` khi được bàn giao. Bản trên đĩa trước Phase 3 dùng thời lượng 300, 330, 360 giây và thắng khi thắp hết đèn.
