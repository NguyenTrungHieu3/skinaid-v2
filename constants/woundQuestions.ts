// constants/woundQuestions.ts
// ─── Bộ câu hỏi trắc nghiệm theo từng loại vết thương ─────────────
// Dữ liệu gốc từ file Bộ_câu_hỏi_export.xlsx

export interface QuestionOption {
  id: string;
  label: string;
  triageLevel: 'nhẹ' | 'trung bình' | 'nặng';
}

export interface WoundQuestion {
  id: string;
  order: number;
  questionText: string;       // Tiêu đề câu hỏi
  isMultipleChoice: boolean;  // true = chọn nhiều, false = chọn 1
  options: QuestionOption[];
}

export interface WoundQuestionSet {
  woundTypeId: string;   // "tray", "bam", "bong", "mun-trung-ca", "vay-nen", "nam-da"
  woundTypeName: string; // Tên hiển thị
  description: string;
  questions: WoundQuestion[];
}

// ─── 6 bộ câu hỏi ────────────────────────────────────────────────

export const WOUND_QUESTION_SETS: WoundQuestionSet[] = [
  // ── 1. BỎNG ─────────────────────────────────────────────────────
  {
    woundTypeId: 'bong',
    woundTypeName: 'Bỏng',
    description: 'Đánh giá mức độ nghiêm trọng của vết bỏng dựa trên màu sắc da, mức độ phồng rộp và diện tích bị ảnh hưởng.',
    questions: [
      {
        id: 'bong_q1',
        order: 1,
        questionText: 'Hình dạng da',
        isMultipleChoice: false,
        options: [
          { id: 'bong_q1_a1', label: 'Đỏ, không phồng', triageLevel: 'nhẹ' },
          { id: 'bong_q1_a2', label: 'Đỏ, phồng nước nhỏ', triageLevel: 'trung bình' },
          { id: 'bong_q1_a3', label: 'Nhiều bóng nước / đã vỡ', triageLevel: 'trung bình' },
          { id: 'bong_q1_a4', label: 'Trắng/xám, khô, ít đau', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'bong_q2',
        order: 2,
        questionText: 'Diện tích',
        isMultipleChoice: false,
        options: [
          { id: 'bong_q2_a1', label: 'Nhỏ hơn 1 bàn tay', triageLevel: 'nhẹ' },
          { id: 'bong_q2_a2', label: '1–3 bàn tay', triageLevel: 'trung bình' },
          { id: 'bong_q2_a3', label: '3–10 bàn tay', triageLevel: 'nặng' },
          { id: 'bong_q2_a4', label: 'Hơn 10 bàn tay', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'bong_q3',
        order: 3,
        questionText: 'Vị trí',
        isMultipleChoice: true,
        options: [
          { id: 'bong_q3_a1', label: 'Thân/chi, xa khớp lớn', triageLevel: 'nhẹ' },
          { id: 'bong_q3_a2', label: 'Gần khớp lớn', triageLevel: 'trung bình' },
          { id: 'bong_q3_a3', label: 'Mặt/cổ/tay/chân/sinh dục', triageLevel: 'nặng' },
          { id: 'bong_q3_a4', label: 'Nhiều vùng, có mặt/cổ/ngực', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'bong_q4',
        order: 4,
        questionText: 'Nguyên nhân',
        isMultipleChoice: false,
        options: [
          { id: 'bong_q4_a1', label: 'Nước / đồ uống nóng', triageLevel: 'nhẹ' },
          { id: 'bong_q4_a2', label: 'Lửa / dầu / hơi nóng', triageLevel: 'trung bình' },
          { id: 'bong_q4_a3', label: 'Hóa chất', triageLevel: 'nặng' },
          { id: 'bong_q4_a4', label: 'Điện', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'bong_q5',
        order: 5,
        questionText: 'Triệu chứng kèm',
        isMultipleChoice: true,
        options: [
          { id: 'bong_q5_a1', label: 'Chỉ đau tại chỗ', triageLevel: 'nhẹ' },
          { id: 'bong_q5_a2', label: 'Đau nhiều nhưng tỉnh táo', triageLevel: 'trung bình' },
          { id: 'bong_q5_a3', label: 'Khó thở / ho khò khè', triageLevel: 'nặng' },
          { id: 'bong_q5_a4', label: 'Choáng, lả mờ', triageLevel: 'nặng' },
        ],
      },
    ],
  },

  // ── 2. TRẦY XƯỚc ─────────────────────────────────────────────────
  {
    woundTypeId: 'tray',
    woundTypeName: 'Trầy xước',
    description: 'Xác định mức độ tổn thương bề mặt da do ma sát hoặc va chạm, đánh giá nguy cơ nhiễm trùng và nhu cầu chăm sóc vết thương.',
    questions: [
      {
        id: 'tray_q1',
        order: 1,
        questionText: 'Độ sâu',
        isMultipleChoice: false,
        options: [
          { id: 'tray_q1_a1', label: 'Xước nông, ít máu', triageLevel: 'nhẹ' },
          { id: 'tray_q1_a2', label: 'Nông nhưng rộng', triageLevel: 'trung bình' },
          { id: 'tray_q1_a3', label: 'Thấy mỡ vàng, máu rỉ', triageLevel: 'trung bình' },
          { id: 'tray_q1_a4', label: 'Rất sâu, nghi lộ gân/xương', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'tray_q2',
        order: 2,
        questionText: 'Độ sạch',
        isMultipleChoice: false,
        options: [
          { id: 'tray_q2_a1', label: 'Gần như sạch', triageLevel: 'nhẹ' },
          { id: 'tray_q2_a2', label: 'Bụi/cát, rửa ra được', triageLevel: 'nhẹ' },
          { id: 'tray_q2_a3', label: 'Dị vật khó lấy', triageLevel: 'trung bình' },
          { id: 'tray_q2_a4', label: 'Vật to/dài cắm sâu', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'tray_q3',
        order: 3,
        questionText: 'Đau & cử động',
        isMultipleChoice: false,
        options: [
          { id: 'tray_q3_a1', label: 'Đau nhẹ, cử động bình thường', triageLevel: 'nhẹ' },
          { id: 'tray_q3_a2', label: 'Đau vừa, hơi khó cử động', triageLevel: 'trung bình' },
          { id: 'tray_q3_a3', label: 'Đau nhiều, khó cử động', triageLevel: 'trung bình' },
          { id: 'tray_q3_a4', label: 'Tê / mất cảm giác', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'tray_q4',
        order: 4,
        questionText: 'Diễn tiến',
        isMultipleChoice: false,
        options: [
          { id: 'tray_q4_a1', label: '< 1 ngày, ko đỏ lan', triageLevel: 'nhẹ' },
          { id: 'tray_q4_a2', label: '1–3 ngày, hơi đỏ', triageLevel: 'nhẹ' },
          { id: 'tray_q4_a3', label: 'Đỏ lan, đau tăng', triageLevel: 'trung bình' },
          { id: 'tray_q4_a4', label: 'Mưng mủ / sốt', triageLevel: 'nặng' },
        ],
      },
    ],
  },

  // ── 3. BẦM TÍM ───────────────────────────────────────────────────
  {
    woundTypeId: 'bam',
    woundTypeName: 'Bầm tím',
    description: 'Đánh giá tình trạng tụ máu dưới da do chấn thương dựa trên màu sắc, kích thước và mức độ đau để xác định mức độ nghiêm trọng.',
    questions: [
      {
        id: 'bam_q1',
        order: 1,
        questionText: 'Kích thước',
        isMultipleChoice: false,
        options: [
          { id: 'bam_q1_a1', label: 'Nhỏ hơn đồng xu', triageLevel: 'nhẹ' },
          { id: 'bam_q1_a2', label: 'Cỡ bàn tay', triageLevel: 'trung bình' },
          { id: 'bam_q1_a3', label: 'Lớn hơn bàn tay', triageLevel: 'trung bình' },
          { id: 'bam_q1_a4', label: 'Nhiều chỗ khác nhau', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'bam_q2',
        order: 2,
        questionText: 'Đau & vận động',
        isMultipleChoice: false,
        options: [
          { id: 'bam_q2_a1', label: 'Đau nhẹ, vẫn sinh hoạt', triageLevel: 'nhẹ' },
          { id: 'bam_q2_a2', label: 'Đau vừa, hạn chế nhẹ', triageLevel: 'trung bình' },
          { id: 'bam_q2_a3', label: 'Đau nhiều, khó cử động', triageLevel: 'trung bình' },
          { id: 'bam_q2_a4', label: 'Đau tăng nhanh, sợ rất căng', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'bam_q3',
        order: 3,
        questionText: 'Nguyên nhân',
        isMultipleChoice: false,
        options: [
          { id: 'bam_q3_a1', label: 'Va nhẹ / tự nhẹ', triageLevel: 'nhẹ' },
          { id: 'bam_q3_a2', label: 'Va mạnh / tự vừa', triageLevel: 'trung bình' },
          { id: 'bam_q3_a3', label: 'Tai nạn nặng', triageLevel: 'nặng' },
          { id: 'bam_q3_a4', label: 'Không nhớ bị va', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'bam_q4',
        order: 4,
        questionText: 'Toàn thân',
        isMultipleChoice: true,
        options: [
          { id: 'bam_q4_a1', label: 'Không có gì khác', triageLevel: 'nhẹ' },
          { id: 'bam_q4_a2', label: 'Mệt nhẹ', triageLevel: 'nhẹ' },
          { id: 'bam_q4_a3', label: 'Sốt / chóng mặt', triageLevel: 'trung bình' },
          { id: 'bam_q4_a4', label: 'Dễ chảy máu (cam, chân răng)', triageLevel: 'nặng' },
        ],
      },
    ],
  },

  // ── 4. NẤM DA ─────────────────────────────────────────────────────
  {
    woundTypeId: 'nam-da',
    woundTypeName: 'Nấm da',
    description: 'Xác định dấu hiệu nhiễm nấm trên da như ngứa, lan rộng, viền tổn thương để đưa ra hướng xử lý và phòng tránh lây lan.',
    questions: [
      {
        id: 'namda_q1',
        order: 1,
        questionText: 'Hình dạng',
        isMultipleChoice: false,
        options: [
          { id: 'namda_q1_a1', label: 'Vòng tròn, rìa đỏ, giữa nhạt', triageLevel: 'nhẹ' },
          { id: 'namda_q1_a2', label: 'Mảng đỏ, rìa mờ', triageLevel: 'trung bình' },
          { id: 'namda_q1_a3', label: 'Mảng dày, vảy trắng/bạc', triageLevel: 'trung bình' },
          { id: 'namda_q1_a4', label: 'Chấm/mụn quanh lỗ chân lông', triageLevel: 'trung bình' },
        ],
      },
      {
        id: 'namda_q2',
        order: 2,
        questionText: 'Vị trí',
        isMultipleChoice: true,
        options: [
          { id: 'namda_q2_a1', label: 'Thân, đùi, bẹn, kẽ chân', triageLevel: 'nhẹ' },
          { id: 'namda_q2_a2', label: 'Mặt, nếp gấp tay/chân', triageLevel: 'trung bình' },
          { id: 'namda_q2_a3', label: 'Khuỷu, gối, da đầu', triageLevel: 'trung bình' },
          { id: 'namda_q2_a4', label: 'Mặt, ngực, lưng', triageLevel: 'trung bình' },
        ],
      },
      {
        id: 'namda_q3',
        order: 3,
        questionText: 'Cảm giác',
        isMultipleChoice: false,
        options: [
          { id: 'namda_q3_a1', label: 'Ngứa nhiều, ẩm nóng', triageLevel: 'trung bình' },
          { id: 'namda_q3_a2', label: 'Hơi ngứa, có thể ướt', triageLevel: 'nhẹ' },
          { id: 'namda_q3_a3', label: 'Khô, nứt, ít ngứa', triageLevel: 'nhẹ' },
          { id: 'namda_q3_a4', label: 'Đau, có mụn mủ', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'namda_q4',
        order: 4,
        questionText: 'Lan & thời gian',
        isMultipleChoice: false,
        options: [
          { id: 'namda_q4_a1', label: '1–2 mảng, vài tuần', triageLevel: 'nhẹ' },
          { id: 'namda_q4_a2', label: 'Nhiều mảng, lan nhanh', triageLevel: 'trung bình' },
          { id: 'namda_q4_a3', label: 'Tái phát nhiều tháng/năm', triageLevel: 'trung bình' },
          { id: 'namda_q4_a4', label: 'Lan rất nhanh, đỏ đau', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'namda_q5',
        order: 5,
        questionText: 'Thuốc đã dùng',
        isMultipleChoice: false,
        options: [
          { id: 'namda_q5_a1', label: 'Chưa dùng', triageLevel: 'nhẹ' },
          { id: 'namda_q5_a2', label: 'Kem chống nấm ≥2 tuần', triageLevel: 'trung bình' },
          { id: 'namda_q5_a3', label: 'Kem "dễ ứng" có corticoid', triageLevel: 'trung bình' },
          { id: 'namda_q5_a4', label: 'Không rõ / nhiều loại trộn', triageLevel: 'nặng' },
        ],
      },
    ],
  },

  // ── 5. MỤN TRỨNG CÁ ───────────────────────────────────────────────
  {
    woundTypeId: 'mun-trung-ca',
    woundTypeName: 'Mụn trứng cá',
    description: 'Đánh giá tình trạng viêm da liên quan đến tuyến bã nhờn dựa trên số lượng, loại mụn và mức độ lan rộng để xác định mức độ cần chăm sóc hoặc điều trị.',
    questions: [
      {
        id: 'mun_q1',
        order: 1,
        questionText: 'Loại mụn',
        isMultipleChoice: true,
        options: [
          { id: 'mun_q1_a1', label: 'Đầu đen/đầu trắng là chính', triageLevel: 'nhẹ' },
          { id: 'mun_q1_a2', label: 'Nhiều mụn đỏ/mủ', triageLevel: 'trung bình' },
          { id: 'mun_q1_a3', label: 'Nhiều mụn bọc, u, sẹo', triageLevel: 'nặng' },
          { id: 'mun_q1_a4', label: 'Chủ yếu mảng đỏ/vảy', triageLevel: 'trung bình' },
        ],
      },
      {
        id: 'mun_q2',
        order: 2,
        questionText: 'Vị trí',
        isMultipleChoice: true,
        options: [
          { id: 'mun_q2_a1', label: 'Trán, mũi, cằm', triageLevel: 'nhẹ' },
          { id: 'mun_q2_a2', label: 'Mặt + ít ở lưng/ngực', triageLevel: 'trung bình' },
          { id: 'mun_q2_a3', label: 'Nhiều ở mặt, lưng, ngực', triageLevel: 'nặng' },
          { id: 'mun_q2_a4', label: 'Chủ yếu vùng khác (bẹn, tay)', triageLevel: 'trung bình' },
        ],
      },
      {
        id: 'mun_q3',
        order: 3,
        questionText: 'Thời gian',
        isMultipleChoice: false,
        options: [
          { id: 'mun_q3_a1', label: 'Vài tuần', triageLevel: 'nhẹ' },
          { id: 'mun_q3_a2', label: 'Vài tháng', triageLevel: 'trung bình' },
          { id: 'mun_q3_a3', label: '> 6 tháng, nặng dần', triageLevel: 'nặng' },
          { id: 'mun_q3_a4', label: 'Bùng phát nhanh vài ngày', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'mun_q4',
        order: 4,
        questionText: 'Ảnh hưởng tâm lý',
        isMultipleChoice: false,
        options: [
          { id: 'mun_q4_a1', label: 'Hơi mất tự tin', triageLevel: 'nhẹ' },
          { id: 'mun_q4_a2', label: 'Ngại giao tiếp', triageLevel: 'trung bình' },
          { id: 'mun_q4_a3', label: 'Tránh gặp người khác', triageLevel: 'trung bình' },
          { id: 'mun_q4_a4', label: 'Nghĩ đến làm hại bản thân', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'mun_q5',
        order: 5,
        questionText: 'Điều trị đã dùng',
        isMultipleChoice: false,
        options: [
          { id: 'mun_q5_a1', label: 'Chỉ rửa mặt', triageLevel: 'nhẹ' },
          { id: 'mun_q5_a2', label: 'Mỹ phẩm/OTC chuẩn >6 tuần', triageLevel: 'trung bình' },
          { id: 'mun_q5_a3', label: 'Kem trộn / tẩy trắng', triageLevel: 'nặng' },
          { id: 'mun_q5_a4', label: 'Đang theo đơn bác sĩ', triageLevel: 'trung bình' },
        ],
      },
    ],
  },

  // ── 6. VẢY NẾN ────────────────────────────────────────────────────
  {
    woundTypeId: 'vay-nen',
    woundTypeName: 'Vảy nến',
    description: 'Đánh giá tình trạng da liên quan đến vảy nến dựa trên mức độ lan rộng, bong tróc và triệu chứng đi kèm nhằm xác định mức độ cần theo dõi hoặc điều trị.',
    questions: [
      {
        id: 'vaynen_q1',
        order: 1,
        questionText: 'Hình dạng',
        isMultipleChoice: false,
        options: [
          { id: 'vaynen_q1_a1', label: 'Mảng đỏ/tím, vảy trắng/bạc dày', triageLevel: 'trung bình' },
          { id: 'vaynen_q1_a2', label: 'Mảng đỏ ẩm, ít vảy', triageLevel: 'trung bình' },
          { id: 'vaynen_q1_a3', label: 'Vòng tròn, rìa đỏ, giữa nhạt', triageLevel: 'nhẹ' },
          { id: 'vaynen_q1_a4', label: 'Nốt/mụn nhỏ', triageLevel: 'nhẹ' },
        ],
      },
      {
        id: 'vaynen_q2',
        order: 2,
        questionText: 'Vị trí',
        isMultipleChoice: true,
        options: [
          { id: 'vaynen_q2_a1', label: 'Khuỷu, gối, da đầu, lưng', triageLevel: 'trung bình' },
          { id: 'vaynen_q2_a2', label: 'Nếp gấp, bẹn', triageLevel: 'trung bình' },
          { id: 'vaynen_q2_a3', label: 'Bẹn, kẽ chân, thân', triageLevel: 'nhẹ' },
          { id: 'vaynen_q2_a4', label: 'Chủ yếu một dạng mụn', triageLevel: 'nhẹ' },
        ],
      },
      {
        id: 'vaynen_q3',
        order: 3,
        questionText: 'Diện tích',
        isMultipleChoice: false,
        options: [
          { id: 'vaynen_q3_a1', label: '1–2 mảng nhỏ', triageLevel: 'nhẹ' },
          { id: 'vaynen_q3_a2', label: 'Nhiều vùng nhưng không toàn thân', triageLevel: 'trung bình' },
          { id: 'vaynen_q3_a3', label: 'Gần như khắp cơ thể', triageLevel: 'nặng' },
          { id: 'vaynen_q3_a4', label: 'Thay đổi rất nhanh', triageLevel: 'nặng' },
        ],
      },
      {
        id: 'vaynen_q4',
        order: 4,
        questionText: 'Triệu chứng kèm',
        isMultipleChoice: true,
        options: [
          { id: 'vaynen_q4_a1', label: 'Hơi ngứa/căng', triageLevel: 'nhẹ' },
          { id: 'vaynen_q4_a2', label: 'Ngứa nhiều, mất ngủ', triageLevel: 'trung bình' },
          { id: 'vaynen_q4_a3', label: 'Sốt, rét run, mệt', triageLevel: 'nặng' },
          { id: 'vaynen_q4_a4', label: 'Đau/cứng khớp', triageLevel: 'trung bình' },
        ],
      },
      {
        id: 'vaynen_q5',
        order: 5,
        questionText: 'Thời gian',
        isMultipleChoice: false,
        options: [
          { id: 'vaynen_q5_a1', label: 'Vài tuần', triageLevel: 'nhẹ' },
          { id: 'vaynen_q5_a2', label: 'Nhiều tháng/năm', triageLevel: 'trung bình' },
          { id: 'vaynen_q5_a3', label: 'Đang điều trị vảy nến', triageLevel: 'trung bình' },
          { id: 'vaynen_q5_a4', label: 'Dùng nhiều kem có corticoid', triageLevel: 'nặng' },
        ],
      },
    ],
  },
];

/** Tìm bộ câu hỏi theo woundTypeId */
export function getQuestionSetByTypeId(woundTypeId: string): WoundQuestionSet | undefined {
  return WOUND_QUESTION_SETS.find((s) => s.woundTypeId === woundTypeId);
}

/** Lấy nhiều bộ câu hỏi theo danh sách woundTypeIds (loại trùng) */
export function getQuestionSetsForWounds(woundTypeIds: string[]): WoundQuestionSet[] {
  const unique = [...new Set(woundTypeIds)];
  return unique
    .map((id) => getQuestionSetByTypeId(id))
    .filter((s): s is WoundQuestionSet => s !== undefined);
}
