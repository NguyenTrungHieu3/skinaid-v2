# FC1 — Wound Analysis & First-Aid Result: API Integration Guide

> **Đọc file này cùng với `CLAUDE.md` (project memory).** File này chỉ mô tả luồng API cho FC1.  
> Base URL: `http://52.20.177.68/api/v1`  
> HTTP client: `api/axiosClient.ts` (tự động gắn `Authorization: Bearer <token>` cho mọi request).

---

## 0. Tổng quan luồng FC1

### Luồng chính (LLM hoạt động bình thường)

```
[Camera / Gallery]
       │  uri
       ▼
image-check.tsx          ← quality gate (đã có, không thay đổi)
       │  uri (passed)
       ▼
analyzing.tsx            ← [TODO-1] gọi POST /ai/analyze
       │  analysis_id + raw detections
       ▼
analysis-result.tsx      ← [TODO-2] gọi GET /ai/analysis/{analysis_id}
       │  selectedDetections[] (có firstaid_snapshot)
       ▼
wound-assessment.tsx     ← [TODO-3] gọi POST /wound-responses/resolve-questionnaires
       │  answers[]
       ▼
assessment-loading.tsx   ← [TODO-4] gọi POST /wound-responses/submit (forward_to_synthesis=true)
       │
       ▼
assessment-result.tsx    ← [TODO-5] hiển thị kết quả từ LLM synthesis
```

### Luồng fallback (LLM KHÔNG hoạt động)

```
analyzing.tsx            ← POST /ai/analyze
       │
       ▼
analysis-result.tsx      ← GET /ai/analysis/{id}  ← firstaid_snapshot có sẵn tại đây
       │  selectedDetections[] (có firstaid_snapshot)
       │
       │  ⚠️ BỎ QUA HOÀN TOÀN wound-assessment + assessment-loading
       │
       ▼
assessment-result.tsx    ← hiển thị trực tiếp từ firstaid_snapshot (không cần questionnaire)
```

> **Quyết định fallback xảy ra tại `analysis-result.tsx`**, ngay sau khi fetch API-2.  
> Nếu LLM không khả dụng (xác định bằng flag/header từ API-2 hoặc thử submit trước), app bỏ qua bước câu hỏi và điều hướng thẳng sang kết quả dùng `firstaid_snapshot`.

---

## 1. Authentication

**Chỉ hỗ trợ user đã đăng nhập (JWT Bearer).** Không có guest mode.

`axiosClient.ts` đã tự động gắn `Authorization: Bearer <token>` vào mọi request thông qua request interceptor. Không cần xử lý thêm gì ở tầng screen.

```ts
// axiosClient.ts — đã có sẵn, KHÔNG sửa
// Interceptor tự lấy token từ storage và gắn vào header trước mỗi request.
// Nếu token hết hạn hoặc không tồn tại → 401 → redirect login (đã có).
```

> **Không truyền `user_id` hay `session_id` thủ công vào payload** — BE tự xác định user qua JWT token trong header.

---

## 2. Tạo `services/woundService.ts` (file mới)

Tập trung tất cả API calls của FC1. **Không** viết fetch trực tiếp trong screen.

```ts
// services/woundService.ts
import axiosClient from '../api/axiosClient';
import { getErrorMessage } from './utils';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AnalyzeResponse {
  analysis_id: string;
  image_url: string;
  file_name: string;
  total_detections: number;
  ai_model_version: string;
  analyzed_at: string;
}

export interface FirstAidSnapshot {
  title: string;
  steps: string[];
  dos: string[];
  donts: string[];
  supplies_needed: string[];
  estimated_healing_time: string;
  source: string | null;
}

export interface SignificantWound {
  detection_id: string;
  wound_type: string;          // 'abrasion' | 'bruise' | 'burn' | 'acne' | 'psoriasis' | 'fungal'
  severity: string;            // 'mild' | 'moderate' | 'severe'
  sub_type: string | null;
  confidence_score: number;    // 0–1
  bounding_box: { x: number; y: number; width: number; height: number };
  detection_index: number;
  firstaid_guide_id: string;
  firstaid_snapshot: FirstAidSnapshot; // ← fallback hoàn chỉnh khi LLM không hoạt động
}

export interface AnalysisDetailResponse {
  analysis_id: string;
  image_url: string;
  file_name: string;
  total_detections: number;
  significant_wounds: SignificantWound[];
  analyzed_at: string;
}

export interface QuestionnaireAnswer {
  answer_id: string;
  answer_text: string;
  triage_level: 'green' | 'yellow' | 'red';
  order_index: number;
  question_id: string;
}

export interface QuestionnaireQuestion {
  question_id: string;
  question_text: string;
  order_index: number;
  is_multiple_choice: boolean;
  answers: QuestionnaireAnswer[];
}

export interface ResolvedQuestionnaire {
  wound_type: string;
  subtype: string | null;
  severity: string;
  representative_detection_id: string;
  detection_count: number;
  questionnaire: {
    questionnaire_id: string;
    wound_type: string;
    title: string;
    description: string;
    questions: QuestionnaireQuestion[]; // số câu là động, tùy wound_type
  };
}

export interface SubmitDetection {
  detection_id: string;
  wound_type: string;
  subtype: string | null;
  severity: string;
  confidence: number;
}

export interface SubmitAnswer {
  question_id: string;
  answer_ids: string[];
}

export interface SynthesisResult {
  wound_type: string;
  subtype: string | null;
  severity: string;
  source: 'llm' | 'db' | 'fallback';
  guidance: string;
  structured_guidance: {
    title: string;
    steps: string[];
    dos: string[];
    donts: string[];
    supplies_needed: string[];
    estimated_healing_time: string;
  } | null;
  validated: boolean;
  error: string | null;
}

export interface SubmitResponse {
  aggregated_triage: 'green' | 'yellow' | 'red';
  selections: Array<{
    question_id: string;
    answer_ids: string[];
    triage_levels: string[];
  }>;
  syntheses: SynthesisResult[];
}

// ─── API calls ────────────────────────────────────────────────────────────────

/**
 * [API-1] Gửi ảnh để AI phân tích nhận diện vết thương.
 * Dùng multipart/form-data với field tên "file".
 */
export async function analyzeWoundImage(imageUri: string): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    name: `wound_${Date.now()}.jpg`,
    type: 'image/jpeg',
  } as unknown as Blob);

  const response = await axiosClient.post('/ai/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data.data as AnalyzeResponse;
}

/**
 * [API-2] Lấy chi tiết kết quả phân tích.
 * Response chứa firstaid_snapshot trong mỗi SignificantWound —
 * đây là nguồn dữ liệu sơ cứu dùng khi LLM fallback.
 */
export async function getAnalysisDetail(analysisId: string): Promise<AnalysisDetailResponse> {
  const response = await axiosClient.get(`/ai/analysis/${analysisId}`);
  return response.data.data as AnalysisDetailResponse;
}

/**
 * [API-3] Resolve bộ câu hỏi tương ứng với các vết thương người dùng đã chọn.
 * Dedupe theo (wound_type, subtype) — mỗi cặp duy nhất 1 bộ câu hỏi.
 * Số câu hỏi trả về là động (tùy wound_type), không hardcode.
 */
export async function resolveQuestionnaires(
  detections: SubmitDetection[]
): Promise<ResolvedQuestionnaire[]> {
  const response = await axiosClient.post('/wound-responses/resolve-questionnaires', {
    detections,
  });
  return response.data.data.questionnaires as ResolvedQuestionnaire[];
}

/**
 * [API-4] Submit câu trả lời + tổng hợp kết quả sơ cứu qua LLM.
 * forward_to_synthesis=true  → LLM tổng hợp (nếu LLM available).
 * forward_to_synthesis=false → chỉ validate answers, không gọi LLM.
 */
export async function submitWoundResponses(payload: {
  analysis_id: string;
  user_description?: string;
  detections: SubmitDetection[];
  answers: SubmitAnswer[];
  forward_to_synthesis: boolean;
}): Promise<SubmitResponse> {
  const response = await axiosClient.post('/wound-responses/submit', payload);
  return response.data.data as SubmitResponse;
}
```

---

## 3. TODO-1 — `analyzing.tsx`: Thay setTimeout bằng API call thực

### Hiện tại (xóa đi):
```ts
// ❌ MOCK — xóa toàn bộ setTimeout này
setTimeout(() => {
  router.push({ pathname: '/analysis-result', params: { uri } });
}, 4000);
```

### Thay bằng:
```ts
// ✅ REAL — trong analyzing.tsx
import { analyzeWoundImage } from '../services/woundService';

useEffect(() => {
  let cancelled = false;

  async function runAnalysis() {
    try {
      const result = await analyzeWoundImage(uri); // uri từ route params
      if (cancelled) return;

      router.replace({
        pathname: '/analysis-result',
        params: {
          uri,
          analysisId: result.analysis_id,
        },
      });
    } catch (error) {
      if (cancelled) return;
      const msg = getErrorMessage(error);
      Alert.alert('Lỗi phân tích', msg, [
        { text: 'Thử lại', onPress: runAnalysis },
        { text: 'Hủy', onPress: () => router.back() },
      ]);
    }
  }

  runAnalysis();
  return () => { cancelled = true; };
}, []);
```

> **Lưu ý:** Không đặt timeout cứng. API response là event xác định thời điểm navigate.  
> `AnalyzingLoader` component vẫn chạy animation trong khi await API.

---

## 4. TODO-2 — `analysis-result.tsx`: Hiển thị dữ liệu thực + quyết định luồng

### Params nhận vào (thêm `analysisId`):
```ts
const { uri, analysisId } = useLocalSearchParams<{ uri: string; analysisId: string }>();
```

### Fetch data thực (thay MOCK_ANALYSIS_RESULT):
```ts
import { getAnalysisDetail, SignificantWound } from '../services/woundService';

const [analysisDetail, setAnalysisDetail] = useState<AnalysisDetailResponse | null>(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  async function fetchDetail() {
    try {
      const detail = await getAnalysisDetail(analysisId);
      setAnalysisDetail(detail);
    } catch (err) {
      Alert.alert('Không thể tải kết quả', getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }
  fetchDetail();
}, [analysisId]);
```

### Map API response → kiểu DetectedWound hiện tại:
```ts
function mapToDetectedWounds(wounds: SignificantWound[]): DetectedWound[] {
  return wounds.map(w => ({
    id: w.detection_id,
    woundTypeId: mapWoundType(w.wound_type),
    label: mapWoundLabel(w.wound_type),
    confidence: Math.round(w.confidence_score * 100),
    severity: w.severity,
    boundingBox: w.bounding_box,
    selected: false,
  }));
}
```

### Bảng mapping wound_type API → woundTypeId FE:
| API `wound_type` | FE `woundTypeId` | Label hiển thị |
|---|---|---|
| `abrasion` | `tray` | Trầy xước |
| `bruise` | `bam` | Bầm tím |
| `burn` | `bong` | Bỏng |
| `acne` | `mun-trung-ca` | Mụn trứng cá |
| `psoriasis` | `vay-nen` | Vảy nến |
| `fungal` | `nam-da` | Nấm da |

```ts
const WOUND_TYPE_MAP: Record<string, string> = {
  abrasion: 'tray', bruise: 'bam', burn: 'bong',
  acne: 'mun-trung-ca', psoriasis: 'vay-nen', fungal: 'nam-da',
};
const WOUND_LABEL_MAP: Record<string, string> = {
  abrasion: 'Trầy xước', bruise: 'Bầm tím', burn: 'Bỏng',
  acne: 'Mụn trứng cá', psoriasis: 'Vảy nến', fungal: 'Nấm da',
};
function mapWoundType(t: string) { return WOUND_TYPE_MAP[t] ?? t; }
function mapWoundLabel(t: string) { return WOUND_LABEL_MAP[t] ?? t; }
```

### Summary card (Số lượng, Độ chính xác TB, Loại, Nghiêm trọng):
```ts
// Số lượng: analysisDetail.total_detections
// Độ chính xác TB: average confidence_score * 100 của significant_wounds
// Loại: wound label của wound đầu tiên (hoặc "Nhiều loại" nếu >1 loại khác nhau)
// Nghiêm trọng: severity cao nhất (severe > moderate > mild)
const avgConfidence = wounds.reduce((sum, w) => sum + w.confidence_score, 0) / wounds.length;
```

### Navigate khi user bấm "Tiếp tục":

```ts
// selectedWounds = SignificantWound[] mà user đã tick chọn
const selectedWounds = analysisDetail.significant_wounds.filter(w =>
  selectedIds.includes(w.detection_id)
);
const selectedDetectionsJson = JSON.stringify(selectedWounds); // giữ nguyên firstaid_snapshot

// ⚠️ Kiểm tra LLM availability trước khi quyết định luồng
// (xem mục "Quyết định LLM fallback tại analysis-result" bên dưới)
```

### Quyết định LLM fallback tại `analysis-result.tsx`:

Đây là điểm quyết định luồng duy nhất. Thực hiện sau khi user chọn xong vết thương và bấm "Tiếp tục":

```ts
async function handleContinue() {
  const selectedWounds = analysisDetail!.significant_wounds.filter(w =>
    selectedIds.includes(w.detection_id)
  );
  const selectedDetectionsJson = JSON.stringify(selectedWounds);

  // Thử resolve questionnaires để kiểm tra LLM/server availability
  // Nếu bước này thất bại hoặc server báo LLM unavailable → đi thẳng sang kết quả
  try {
    const detections = selectedWounds.map(w => ({
      detection_id: w.detection_id,
      wound_type: w.wound_type,
      subtype: w.sub_type,
      severity: w.severity,
      confidence: w.confidence_score,
    }));

    // Thử gọi resolve-questionnaires; nếu thành công → luồng bình thường
    await resolveQuestionnaires(detections); // chỉ để check, kết quả fetch lại ở wound-assessment

    router.push({
      pathname: '/wound-assessment',
      params: {
        analysisId,
        selectedDetections: selectedDetectionsJson,
        imageUri: uri,
      },
    });

  } catch (err) {
    // LLM không hoạt động hoặc questionnaire không khả dụng
    // → Bỏ qua wound-assessment, chuyển thẳng sang kết quả dùng firstaid_snapshot
    router.replace({
      pathname: '/assessment-result',
      params: {
        analysisId,
        selectedDetections: selectedDetectionsJson, // firstaid_snapshot có sẵn trong này
        synthesisJson: '',                          // rỗng = dùng fallback
        imageUri: uri,
      },
    });
  }
}
```

> **Quy tắc fallback:** Khi LLM không hoạt động, app **bỏ qua hoàn toàn** màn hình `wound-assessment` và `assessment-loading`. Kết quả sơ cứu lấy từ `firstaid_snapshot` đã có sẵn trong response của `GET /ai/analysis/{id}` — bao gồm đầy đủ: loại vết thương, mức độ, độ chính xác, thời gian lành, và hướng dẫn sơ cứu. Không cần user xác nhận thêm qua câu hỏi.

---

## 5. TODO-3 — `wound-assessment.tsx`: Dùng câu hỏi thực từ API

### Params nhận vào:
```ts
const { analysisId, selectedDetections: rawDetections, imageUri } =
  useLocalSearchParams<{ analysisId: string; selectedDetections: string; imageUri: string }>();

const selectedDetections: SignificantWound[] = JSON.parse(rawDetections);
```

### Fetch questionnaires thực (thay WOUND_QUESTION_SETS static):
```ts
import { resolveQuestionnaires, ResolvedQuestionnaire } from '../services/woundService';

const [questionnaires, setQuestionnaires] = useState<ResolvedQuestionnaire[]>([]);

useEffect(() => {
  async function fetchQuestionnaires() {
    const detections = selectedDetections.map(w => ({
      detection_id: w.detection_id,
      wound_type: w.wound_type,
      subtype: w.sub_type,
      severity: w.severity,
      confidence: w.confidence_score,
    }));

    try {
      const result = await resolveQuestionnaires(detections);
      setQuestionnaires(result);
    } catch (err) {
      Alert.alert('Lỗi', getErrorMessage(err));
      router.back();
    }
  }
  fetchQuestionnaires();
}, []);
```

### Render câu hỏi:
- **Số câu hỏi là động** — dùng `questionnaire.questions.length` từ API làm tổng, **tuyệt đối không hardcode** con số cụ thể (như "8 câu" hay "5 câu"). Mỗi wound_type khác nhau có thể trả về số lượng câu hỏi và đáp án khác nhau.
- `is_multiple_choice: false` → radio button (chọn 1 đáp án).
- `is_multiple_choice: true` → checkbox (chọn nhiều đáp án).
- Progress bar: `answeredCount / totalQuestions` (totalQuestions tính tổng tất cả câu hỏi của tất cả questionnaires).
- Tabs trên cùng: mỗi `ResolvedQuestionnaire` là 1 tab (ví dụ: "Trầy xước" | "Bầm tím").

### Ví dụ hiển thị progress:
```ts
// Tính tổng số câu hỏi động từ API
const totalQuestions = questionnaires.reduce(
  (sum, q) => sum + q.questionnaire.questions.length, 0
);
const answeredCount = questionnaires.reduce(
  (sum, q) => sum + q.questionnaire.questions.filter(
    question => (answers.get(question.question_id) ?? []).length > 0
  ).length, 0
);

// Hiển thị: "Đã trả lời X / Y câu" (X và Y đều là động)
```

### State lưu câu trả lời:
```ts
// Map: question_id → answer_ids[]
const [answers, setAnswers] = useState<Map<string, string[]>>(new Map());

function handleSelectAnswer(questionId: string, answerId: string, isMultiple: boolean) {
  setAnswers(prev => {
    const next = new Map(prev);
    if (isMultiple) {
      const current = next.get(questionId) ?? [];
      next.set(questionId, current.includes(answerId)
        ? current.filter(id => id !== answerId)
        : [...current, answerId]
      );
    } else {
      next.set(questionId, [answerId]); // radio: replace
    }
    return next;
  });
}
```

### Điều kiện enable nút hoàn thành:
```ts
// Tất cả questions của tất cả questionnaires phải có ít nhất 1 answer được chọn
const allAnswered = questionnaires.every(q =>
  q.questionnaire.questions.every(question =>
    (answers.get(question.question_id) ?? []).length > 0
  )
);
```

### Navigate sang assessment-loading:
```ts
router.replace({
  pathname: '/assessment-loading',
  params: {
    analysisId,
    selectedDetections: rawDetections,   // truyền nguyên (có firstaid_snapshot)
    answersJson: JSON.stringify(
      Array.from(answers.entries()).map(([question_id, answer_ids]) => ({
        question_id,
        answer_ids,
      }))
    ),
    imageUri,
  },
});
```

---

## 6. TODO-4 — `assessment-loading.tsx`: Gọi submit API

> **Màn hình này chỉ được gọi khi LLM hoạt động bình thường.** Luồng fallback đã được xử lý tại `analysis-result.tsx` và không đi qua đây.

### Params nhận vào:
```ts
const { analysisId, selectedDetections: rawDetections, answersJson, imageUri } =
  useLocalSearchParams<{
    analysisId: string;
    selectedDetections: string;
    answersJson: string;
    imageUri: string;
  }>();
```

### Logic submit:
```ts
import { submitWoundResponses, SubmitResponse, SignificantWound } from '../services/woundService';

const selectedDetections: SignificantWound[] = JSON.parse(rawDetections);
const answers = JSON.parse(answersJson);

useEffect(() => {
  let cancelled = false;

  async function submitAndNavigate() {
    const detections = selectedDetections.map(w => ({
      detection_id: w.detection_id,
      wound_type: w.wound_type,
      subtype: w.sub_type,
      severity: w.severity,
      confidence: w.confidence_score,
    }));

    try {
      const submitResult = await submitWoundResponses({
        analysis_id: analysisId,
        detections,
        answers,
        forward_to_synthesis: true,
      });

      if (cancelled) return;

      // Kiểm tra LLM có thực sự trả về kết quả không
      const llmFailed = submitResult.syntheses.some(
        s => s.error !== null || !s.structured_guidance
      );

      if (llmFailed) {
        // Dùng firstaid_snapshot (đã có sẵn trong rawDetections)
        router.replace({
          pathname: '/assessment-result',
          params: {
            analysisId,
            selectedDetections: rawDetections,
            synthesisJson: '',   // rỗng = fallback sang firstaid_snapshot
            imageUri,
          },
        });
      } else {
        router.replace({
          pathname: '/assessment-result',
          params: {
            analysisId,
            selectedDetections: rawDetections,
            synthesisJson: JSON.stringify(submitResult.syntheses),
            imageUri,
          },
        });
      }

    } catch (err) {
      if (cancelled) return;
      // Hard network error khi submit
      Alert.alert('Không thể tải kết quả', getErrorMessage(err), [
        { text: 'Thử lại', onPress: submitAndNavigate },
        { text: 'Hủy', onPress: () => router.back() },
      ]);
    }
  }

  submitAndNavigate();
  return () => { cancelled = true; };
}, []);
```

---

## 7. TODO-5 — `assessment-result.tsx`: Hiển thị kết quả thực

### Params nhận vào:
```ts
const { analysisId, selectedDetections: rawDetections, synthesisJson, imageUri } =
  useLocalSearchParams<{
    analysisId: string;
    selectedDetections: string;
    synthesisJson: string;   // rỗng ('') = LLM fallback, dùng firstaid_snapshot
    imageUri: string;
  }>();

const selectedDetections: SignificantWound[] = JSON.parse(rawDetections);
// synthesisJson rỗng hoặc không có → dùng firstaid_snapshot
const syntheses: SynthesisResult[] | null =
  synthesisJson ? JSON.parse(synthesisJson) : null;
```

### Build WoundDetail cho từng wound:
```ts
function buildWoundDetail(wound: SignificantWound, synthesis: SynthesisResult | null): WoundDetail {
  // Ưu tiên LLM synthesis; nếu không có thì dùng firstaid_snapshot từ API-2
  const guide = synthesis?.structured_guidance ?? wound.firstaid_snapshot;

  return {
    id: wound.detection_id,
    woundType: mapWoundType(wound.wound_type),
    label: mapWoundLabel(wound.wound_type),
    accuracy: Math.round(wound.confidence_score * 100),
    hasSeverity: true,
    severity: wound.severity,
    severityColor: mapSeverityColor(wound.severity),
    recoveryTime: guide?.estimated_healing_time ?? '—',
    boundingBox: wound.bounding_box,
    imageUri,
    firstAid: buildFirstAidSections(guide),
  };
}

function mapSeverityColor(severity: string): string {
  if (severity === 'severe') return '#EF4444';    // đỏ
  if (severity === 'moderate') return '#F59E0B';  // vàng
  return '#10B981';                               // xanh (mild)
}

function buildFirstAidSections(guide: FirstAidSnapshot | null): FirstAidSection[] {
  if (!guide) return [];
  return [
    {
      title: 'Sơ cứu ngay',
      icon: 'alert-circle',
      steps: guide.steps.slice(0, 2).map(content => ({ content })),
    },
    {
      title: 'Nên làm',
      icon: 'check-circle',
      steps: guide.dos.map(content => ({ content })),
    },
    {
      title: 'Không nên làm',
      icon: 'x-circle',
      steps: guide.donts.map(content => ({ content })),
    },
  ];
}
```

### Map syntheses theo wound:
```ts
function findSynthesis(wound: SignificantWound, syntheses: SynthesisResult[] | null) {
  if (!syntheses) return null;
  return syntheses.find(
    s => s.wound_type === wound.wound_type && s.subtype === wound.sub_type
  ) ?? null;
}
```

### Build danh sách wound details:
```ts
// Mỗi SignificantWound đã chọn = 1 tab
const woundDetails = selectedDetections.map(w =>
  buildWoundDetail(w, findSynthesis(w, syntheses))
);
// Tab đầu tiên active theo mặc định
```

---

## 8. Error handling toàn luồng

| Bước | Lỗi | Xử lý |
|---|---|---|
| `analyzing.tsx` — POST /ai/analyze | Network / server error | Alert "Lỗi phân tích" + nút Thử lại + Hủy |
| `analysis-result.tsx` — GET /ai/analysis/{id} | 404 / server error | Alert + router.back() |
| `analysis-result.tsx` — kiểm tra LLM availability | LLM không khả dụng | Bỏ qua questionnaire, điều hướng thẳng sang kết quả với firstaid_snapshot |
| `wound-assessment.tsx` — POST /resolve-questionnaires | Error | Alert + router.back() |
| `assessment-loading.tsx` — POST /submit | LLM error (syntheses có `error !== null`) | Fallback sang firstaid_snapshot (không báo lỗi với user) |
| `assessment-loading.tsx` — POST /submit | Hard network error | Alert "Không thể tải kết quả" + nút Thử lại |

```ts
// Pattern chuẩn dùng cho mọi bước:
import { getErrorMessage } from '../services/utils';

try {
  const data = await someApiCall();
  // ...
} catch (error) {
  const message = getErrorMessage(error);
  Alert.alert('Tiêu đề lỗi', message, [...]);
}
```

---

## 9. Checklist tích hợp (theo thứ tự)

- [ ] **Tạo** `services/woundService.ts` với đầy đủ types và 4 hàm API  
- [ ] **`analyzing.tsx`**: xóa setTimeout, thay bằng `analyzeWoundImage()`, truyền `analysisId` sang params  
- [ ] **`analysis-result.tsx`**: thêm param `analysisId`, fetch `getAnalysisDetail()`, map `SignificantWound` → `DetectedWound`; implement `handleContinue()` với logic phân nhánh LLM  
- [ ] **`wound-assessment.tsx`**: thêm params `analysisId` + `selectedDetections`, fetch `resolveQuestionnaires()`, render câu hỏi và đáp án **động** theo API (không hardcode số câu), truyền `answersJson` sang `assessment-loading`  
- [ ] **`assessment-loading.tsx`**: thêm params đầy đủ, gọi `submitWoundResponses()`, xử lý LLM fail → fallback  
- [ ] **`assessment-result.tsx`**: nhận `synthesisJson` (rỗng = fallback), build `WoundDetail` từ synthesis hoặc `firstaid_snapshot`  
- [ ] **Xóa** import `MOCK_ANALYSIS_RESULT` và `WOUND_QUESTION_SETS` khi không còn dùng  
- [ ] **Test** luồng LLM hoạt động bình thường (đi qua questionnaire → submit → kết quả từ synthesis)  
- [ ] **Test** luồng LLM fallback (bỏ qua questionnaire → kết quả từ firstaid_snapshot, hiển thị đầy đủ loại / mức độ / độ chính xác / thời gian lành / sơ cứu)  

---

## 10. Lưu ý quan trọng

1. **Không dùng `router.push()`** cho `assessment-loading → assessment-result`. Dùng `router.replace()` để tránh back về màn hình loading.
2. **Params Expo Router** chỉ nhận `string`. Luôn `JSON.stringify()` array/object khi truyền và `JSON.parse()` khi nhận.
3. **`firstaid_snapshot`** trong `SignificantWound` (từ API-2) là fallback hoàn chỉnh — đủ để hiển thị toàn bộ kết quả (loại, mức độ, độ chính xác, thời gian lành, hướng dẫn sơ cứu) mà không cần bất kỳ input nào thêm từ user. Không gọi thêm API nào khi ở chế độ fallback.
4. **Luồng fallback bỏ qua questionnaire hoàn toàn** — user không thấy màn hình câu hỏi, không cần xác nhận thêm, app điều hướng thẳng sang kết quả.
5. **Số câu hỏi là động** — không hardcode bất kỳ con số nào trong UI. Luôn dùng `questionnaire.questions.length` và `answers.length` từ API response.
6. **Authentication chỉ là JWT Bearer** — không có guest mode. Không truyền `user_id` hay `session_id` trong payload; BE tự xác định user qua token.
7. **Bounding box** từ API trả về pixel tuyệt đối (`{ x, y, width, height }` tính bằng px), cần normalize theo kích thước ảnh gốc khi vẽ overlay.
8. **`wound_type` từ API là tiếng Anh** (`fungal`, `abrasion`...). Dùng `WOUND_TYPE_MAP` và `WOUND_LABEL_MAP` ở mục 4 để convert sang ID/label tiếng Việt đang dùng trong FE.
