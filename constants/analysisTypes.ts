// constants/analysisTypes.ts
// ─── Types cho màn hình kết quả phân tích AI vết thương ──────────

export type SeverityLevel = "NHE" | "TRUNG_BINH" | "NANG";

/** Một vết thương được AI phát hiện trong ảnh */
export interface DetectedWound {
  id: string;              // "wound_1", "wound_2", ...
  index: number;           // 1, 2, 3, ...
  woundType: string;       // "Trầy xước", "Bầm", "Bỏng", ...
  woundTypeId: string;     // "tray", "bam", "bong", ...
  severity?: SeverityLevel; // NHẸ / TRUNG BÌNH / NẶNG — undefined cho vảy nến, nấm da
  confidence: number;      // 0–100 (độ tin cậy %)
  /** Tọa độ bounding box tương đối (0–1) trên ảnh gốc */
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  thumbnailUri?: string;   // crop thumbnail của vùng đó (future)
  selected: boolean;       // User có chọn vết này không
}

/** Kết quả tổng quan từ AI */
export interface AnalysisResult {
  imageUri: string;
  totalWounds: number;
  averageConfidence: number;   // TB độ chính xác (%)
  primaryWoundType: string;    // Loại vết thương chính
  mostSevereWound: string;     // Nghiêm trọng nhất (vd: "Vết T1")
  wounds: DetectedWound[];
}

/** Màu badge theo severity */
export const SEVERITY_CONFIG: Record<
  SeverityLevel,
  { label: string; color: string; bgColor: string }
> = {
  NHE: {
    label: "MỨC ĐỘ: NHẸ",
    color: "#059669",
    bgColor: "#D1FAE5",
  },
  TRUNG_BINH: {
    label: "MỨC ĐỘ: TRUNG BÌNH",
    color: "#D97706",
    bgColor: "#FEF3C7",
  },
  NANG: {
    label: "MỨC ĐỘ: NẶNG",
    color: "#DC2626",
    bgColor: "#FEE2E2",
  },
};

/** Màu thanh progress bar theo confidence */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 70) return "#02A18D"; // teal — cao
  if (confidence >= 40) return "#F59E0B"; // amber — trung bình
  return "#EF4444";                        // red — thấp
}

/** Mock data cho development */
export const MOCK_ANALYSIS_RESULT: AnalysisResult = {
  imageUri: "",
  totalWounds: 3,
  averageConfidence: 54.75,
  primaryWoundType: "Trầy, ...",
  mostSevereWound: "Vết T1",
  wounds: [
    {
      id: "wound_1",
      index: 1,
      woundType: "Trầy xước",
      woundTypeId: "tray",
      severity: "NHE",
      confidence: 74.34,
      boundingBox: { x: 0.1, y: 0.15, width: 0.3, height: 0.28 },
      selected: true,
    },
    {
      id: "wound_2",
      index: 2,
      woundType: "Bầm",
      woundTypeId: "bam",
      severity: "TRUNG_BINH",
      confidence: 99.35,
      boundingBox: { x: 0.45, y: 0.1, width: 0.4, height: 0.35 },
      selected: true,
    },
    {
      id: "wound_3",
      index: 3,
      woundType: "Nấm da",
      woundTypeId: "nam-da",
      confidence: 30.67,
      boundingBox: { x: 0.2, y: 0.55, width: 0.35, height: 0.3 },
      selected: false,
    },
  ],
};

// ─── Types cho màn hình History Detail ───────────────────────────

export interface BoundingBox {
  x: number;       // tỉ lệ so với chiều rộng ảnh (0–1)
  y: number;       // tỉ lệ so với chiều cao ảnh (0–1)
  width: number;   // tỉ lệ
  height: number;  // tỉ lệ
}

export interface FirstAidStep {
  content: string;
}

export interface FirstAidSection {
  title: 'Sơ cứu ngay' | 'Nên làm' | 'Không nên làm';
  icon: 'alert' | 'check' | 'ban';
  steps: FirstAidStep[];
}

export interface WoundDetail {
  id: string;
  woundType: string;       // 'bỏng' | 'trầy' | 'bầm' | 'mụn trứng cá' | 'vảy nến' | 'nấm da'
  label: string;           // VD: 'Bỏng độ 2'
  accuracy: number;        // 0–100
  hasSeverity: boolean;    // false nếu là vảy nến hoặc nấm da
  severity?: 'Nhẹ' | 'Trung bình' | 'Nặng';
  severityColor?: string;
  recoveryTime: string;    // VD: '10-14 ngày'
  firstAid: FirstAidSection[];
  boundingBox: BoundingBox;
  imageUri: string;        // placeholder URI hoặc ảnh thật từ API
  /** Đánh dấu xem có phải đang dùng fallback từ RAG (do LLM lỗi) không */
  isFallback?: boolean;
  /** Câu trả lời bộ câu hỏi đánh giá của người dùng */
  userAnswers?: { questionText: string; selectedOptions: string[] }[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface AnalysisHistoryDetail {
  id: string;
  date: string;
  wounds: WoundDetail[];
  chatHistory: ChatMessage[];
}

// ─── Mock data History Details ────────────────────────────────────

export const MOCK_HISTORY_DETAILS: AnalysisHistoryDetail[] = [
  // Trường hợp 1: 1 vết thương có severity (bỏng)
  {
    id: 'h001',
    date: '18/04/2026',
    wounds: [
      {
        id: 'w001',
        woundType: 'bỏng',
        label: 'Bỏng độ 2',
        accuracy: 94,
        hasSeverity: true,
        severity: 'Nặng',
        severityColor: '#DC2626',
        recoveryTime: '10-14 ngày',
        boundingBox: { x: 0.3, y: 0.2, width: 0.4, height: 0.35 },
        imageUri: 'placeholder',
        userAnswers: [
          { questionText: 'Hình dạng da', selectedOptions: ['Nhiều bóng nước / đã vỡ'] },
          { questionText: 'Diện tích bỏng', selectedOptions: ['1–3 bàn tay'] },
          { questionText: 'Vị trí bỏng', selectedOptions: ['Tay hoặc chân'] },
          { questionText: 'Triệu chứng đi kèm', selectedOptions: ['Đau rát nhiều', 'Sưng tấy vùng bỏng'] },
        ],
        firstAid: [
          {
            title: 'Sơ cứu ngay',
            icon: 'alert',
            steps: [
              { content: 'Rửa vết bỏng dưới vòi nước mát sạch ít nhất 10–15 phút để hạ nhiệt.' },
              { content: 'Tháo nhẹ đồ trang sức, quần áo gần vùng bỏng trước khi sưng lên.' },
            ],
          },
          {
            title: 'Nên làm',
            icon: 'check',
            steps: [
              { content: 'Bôi gel làm dịu (Aloe Vera) và che phủ bằng băng gạc vô trùng.' },
              { content: 'Uống Paracetamol nếu đau nhiều. Đến bệnh viện nếu diện tích lớn.' },
            ],
          },
          {
            title: 'Không nên làm',
            icon: 'ban',
            steps: [
              { content: 'Tuyệt đối không chọc vỡ bọng nước — nguy cơ nhiễm trùng cao.' },
              { content: 'Không dùng nước đá, kem đánh răng hoặc bơ đắp lên vết bỏng.' },
            ],
          },
        ],
      },
    ],
    chatHistory: [
      { id: 'c1', role: 'assistant', content: 'Chào bạn! Tôi là Aidy - trợ lý AI SkinAid. Tôi có thể giúp gì cho bạn?', timestamp: '03/04/2026 09:00' },
      { id: 'c2', role: 'user', content: 'Tôi muốn biết thêm về cách xử lý vết thương bỏng này.', timestamp: '03/04/2026 09:01' },
      { id: 'c3', role: 'assistant', content: 'Để hỗ trợ tốt nhất, bạn có thể mô tả cụ thể vị trí, kích thước, độ sâu của vết thương không?', timestamp: '03/04/2026 09:01' },
    ],
  },

  // Trường hợp 2: 2 vết thương (trầy + bầm)
  {
    id: 'h002',
    date: '15/04/2026',
    wounds: [
      {
        id: 'w002',
        woundType: 'trầy',
        label: 'Trầy xước',
        accuracy: 88,
        hasSeverity: true,
        severity: 'Trung bình',
        severityColor: '#CA8A04',
        recoveryTime: '5-10 ngày',
        boundingBox: { x: 0.1, y: 0.15, width: 0.35, height: 0.3 },
        imageUri: 'placeholder',
        userAnswers: [
          { questionText: 'Vị trí trầy', selectedOptions: ['Tay hoặc chân'] },
          { questionText: 'Mức độ trầy', selectedOptions: ['Chỉ trầy bề mặt da'] },
          { questionText: 'Có chảy máu không', selectedOptions: ['Chảy máu ít, tự cầm'] },
        ],
        firstAid: [
          {
            title: 'Sơ cứu ngay',
            icon: 'alert',
            steps: [
              { content: 'Rửa sạch bằng nước sạch hoặc nước muối sinh lý 0.9%.' },
              { content: 'Loại bỏ bụi bẩn, dị vật nhỏ bằng nhíp đã khử trùng nếu có.' },
            ],
          },
          {
            title: 'Nên làm',
            icon: 'check',
            steps: [
              { content: 'Bôi dung dịch sát khuẩn Povidone-iodine hoặc chlorhexidine lên vùng trầy.' },
              { content: 'Băng lại bằng gạc sạch và thay băng mỗi ngày.' },
            ],
          },
          {
            title: 'Không nên làm',
            icon: 'ban',
            steps: [
              { content: 'Không gãi hoặc cạy lớp vảy đóng trên vết thương khi đang lành.' },
            ],
          },
        ],
      },
      {
        id: 'w003',
        woundType: 'bầm',
        label: 'Vết bầm',
        accuracy: 91,
        hasSeverity: true,
        severity: 'Nhẹ',
        severityColor: '#059669',
        recoveryTime: '7-10 ngày',
        boundingBox: { x: 0.5, y: 0.4, width: 0.3, height: 0.25 },
        imageUri: 'placeholder',
        userAnswers: [
          { questionText: 'Hình thái bầm', selectedOptions: ['Bầm nhỏ dưới 5cm'] },
          { questionText: 'Vị trí bầm', selectedOptions: ['Chi trên (cánh tay, bàn tay)'] },
          { questionText: 'Mức độ đau', selectedOptions: ['Đau nhẹ khi chạm vào'] },
        ],
        firstAid: [
          {
            title: 'Sơ cứu ngay',
            icon: 'alert',
            steps: [
              { content: 'Chườm lạnh ngay bằng túi đá bọc khăn vải trong 20 phút để giảm sưng.' },
            ],
          },
          {
            title: 'Nên làm',
            icon: 'check',
            steps: [
              { content: 'Nâng cao vùng bị bầm nếu ở tay/chân để giảm tụ máu.' },
              { content: 'Sau 48 giờ có thể chườm ấm để tăng tuần hoàn máu.' },
            ],
          },
          {
            title: 'Không nên làm',
            icon: 'ban',
            steps: [
              { content: 'Không xoa bóp mạnh lên vùng bầm trong 24 giờ đầu.' },
            ],
          },
        ],
      },
    ],
    chatHistory: [],
  },

  // Trường hợp 3: vảy nến — không có severity
  {
    id: 'h003',
    date: '10/04/2026',
    wounds: [
      {
        id: 'w004',
        woundType: 'vảy nến',
        label: 'Vảy nến',
        accuracy: 79,
        hasSeverity: false,
        recoveryTime: 'Cần điều trị lâu dài',
        boundingBox: { x: 0.2, y: 0.25, width: 0.45, height: 0.4 },
        imageUri: 'placeholder',
        firstAid: [
          {
            title: 'Nên làm',
            icon: 'check',
            steps: [
              { content: 'Dưỡng ẩm da thường xuyên bằng kem không mùi, không cồn.' },
              { content: 'Tránh gãi hoặc chà xát mạnh lên vùng da bị vảy nến.' },
              { content: 'Đến gặp bác sĩ da liễu để được kê đơn thuốc phù hợp.' },
            ],
          },
          {
            title: 'Không nên làm',
            icon: 'ban',
            steps: [
              { content: 'Không tự ý dùng corticosteroid mạnh mà không có chỉ định của bác sĩ.' },
              { content: 'Tránh tiếp xúc với xà phòng có độ pH cao hoặc hóa chất tẩy rửa.' },
            ],
          },
        ],
      },
    ],
    chatHistory: [
      { id: 'c4', role: 'assistant', content: 'Chào bạn! Tôi là Aidy. Bạn cần tư vấn về tình trạng vảy nến không?', timestamp: '10/04/2026 14:00' },
      { id: 'c5', role: 'user', content: 'Vảy nến có chữa khỏi hẳn được không?', timestamp: '10/04/2026 14:02' },
      { id: 'c6', role: 'assistant', content: 'Vảy nến là bệnh mãn tính, hiện chưa có thuốc chữa khỏi hoàn toàn. Tuy nhiên có thể kiểm soát triệu chứng tốt bằng điều trị đúng cách và thay đổi lối sống.', timestamp: '10/04/2026 14:02' },
    ],
  },
];
