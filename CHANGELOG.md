# Changelog

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

## Phase 2 — Contract v1.1

Ba đêm, số chuẩn, lướt, bùa, Gió Lạc, gió và tạm dừng. Ghi ở tag và bằng chứng `docs/proof/phase-2` khi được bàn giao. Bản trên đĩa trước Phase 3 dùng thời lượng 300, 330, 360 giây và thắng khi thắp hết đèn.
