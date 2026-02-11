# 🎓 Câu hỏi Ôn tập Capstone - Hệ thống AI SkinAid

> **Mục đích:** Chuẩn bị cho buổi thuyết trình Capstone với các câu hỏi thực tế từ Hội đồng

---

## 📋 Mục lục

1. [Kiến trúc & Pipeline](#1-kiến-trúc--pipeline)
2. [YOLO v11 (Detection)](#2-yolo-v11-detection)
3. [EfficientNet B0 (Classification)](#3-efficientnet-b0-classification)
4. [Dataset & Training](#4-dataset--training)
5. [Các loại vết thương](#5-các-loại-vết-thương)
6. [Xử lý Edge Cases](#6-xử-lý-edge-cases)
7. [So sánh với hệ thống khác](#7-so-sánh-với-hệ-thống-khác)
8. [An toàn & Đạo đức](#8-an-toàn--đạo-đức)
9. [Hiệu năng & Deployment](#9-hiệu-năng--deployment)
10. [Tương lai & Phát triển](#10-tương-lai--phát-triển)
11. [Câu hỏi "khó" từ Hội đồng](#11-câu-hỏi-khó-từ-hội-đồng)

---

## 1. Kiến trúc & Pipeline

### Q1: Tại sao sử dụng kiến trúc 2-stage pipeline (YOLO + EfficientNet) thay vì 1 model duy nhất?

**Trả lời:**

Kiến trúc 2-stage pipeline tách biệt 2 nhiệm vụ:

- **Stage 1 (YOLO):** Detection - xác định VỊ TRÍ vết thương
- **Stage 2 (EfficientNet):** Classification - phân loại LOẠI và MỨC ĐỘ

**Lý do:**

1. **Chuyên biệt hóa:** Mỗi model tối ưu cho 1 task cụ thể
2. **Dễ debug:** Có thể kiểm tra từng stage độc lập
3. **Linh hoạt:** Có thể upgrade từng model riêng biệt

**Số liệu chứng minh:**

```python
# analyzer.py
self.detector = WoundDetector(str(yolo_model_path))      # Stage 1
self.classifier = SeverityClassifier(str(efficientnet_model_path))  # Stage 2
```

---

### Q2: Công thức Confidence Fusion là gì? Tại sao chọn trọng số 0.3 và 0.7?

**Trả lời:**

```
final_confidence = yolo_conf × 0.3 + efficientnet_conf × 0.7
```

**Giải thích:**

- EfficientNet được ưu tiên cao hơn (70%) vì nó quyết định kết quả phân loại cuối cùng
- YOLO chỉ chiếm 30% vì nó chỉ xác định vị trí, không phân loại chi tiết

**Số liệu chứng minh:**

```python
# analyzer.py, line 69-70
final_conf = self.getConfidenceFusion(
    detections[i]["confidence"], conf, 0.3, 0.7
)
```

**Ví dụ tính toán:**

- YOLO confidence: 0.90, EfficientNet confidence: 0.50
- Final = 0.90 × 0.3 + 0.50 × 0.7 = 0.27 + 0.35 = **0.62 (62%)**

---

## 2. YOLO v11 (Detection)

### Q3: Tại sao chọn confidence threshold là 0.55 (55%)?

**Trả lời:**

Threshold 0.55 là điểm cân bằng giữa:

- **Precision (độ chính xác):** Không quá thấp để tránh false positive
- **Recall (độ bao phủ):** Không quá cao để không bỏ sót vết thương

**Số liệu chứng minh:**

```python
# config.py
YOLO_CONF_THRESHOLD: float = 0.55
```

**Ý nghĩa thực tế:**

- Dưới 55%: Bỏ qua detection (không đủ tin cậy)
- Từ 55% trở lên: Chấp nhận detection

---

### Q4: YOLO detect bao nhiêu class? Là những class nào?

**Trả lời:**

| Thông số   | Giá trị                                            |
| ---------- | -------------------------------------------------- |
| Số class   | 2                                                  |
| Classes    | `wound` (vết thương), `non-wound` (da bình thường) |
| Model file | model_2_class_v1.pt                                |

---

### Q5: Input size của YOLO là bao nhiêu? Tại sao?

**Trả lời:**

- **Size:** 640 × 640 pixels
- **Lý do:** Đây là size mặc định tối ưu của YOLO, cân bằng giữa accuracy và speed

```python
# config.py
YOLO_IMG_SIZE: int = 640
```

---

## 3. EfficientNet B0 (Classification)

### Q6: Tại sao chọn EfficientNet B0 thay vì B1, B2, B3?

**Trả lời:**

| Variant | Parameters | Accuracy | Speed         |
| ------- | ---------- | -------- | ------------- |
| **B0**  | 5.3M       | Baseline | ⚡ Nhanh nhất |
| B1      | 7.8M       | +1.0%    | Chậm hơn      |
| B2      | 9.2M       | +1.5%    | Chậm hơn      |
| B3      | 12M        | +2.0%    | Chậm hơn      |

**Lý do chọn B0:**

1. Response time yêu cầu ≤10 giây
2. Có thể deploy trên CPU
3. Accuracy đủ tốt cho use case (~65%)

---

### Q7: EfficientNet phân loại bao nhiêu class? Chi tiết từng class?

**Trả lời:** **7 classes**

| #   | Class Name             | Loại    | Mức độ     | Mô tả                        |
| --- | ---------------------- | ------- | ---------- | ---------------------------- |
| 0   | abrasion_mild          | Xây xát | Nhẹ        | Xước bề mặt, ít chảy máu     |
| 1   | abrasion_moderate      | Xây xát | Trung bình | Xước sâu hơn, chảy máu nhiều |
| 2   | bruise_mild            | Bầm tím | Nhẹ        | Bầm nhỏ, màu nhạt            |
| 3   | bruise_moderate        | Bầm tím | Trung bình | Bầm lớn, màu đậm             |
| 4   | burn_mild              | Bỏng    | Nhẹ        | Bỏng độ 1, da đỏ             |
| 5   | burn_moderate_blister  | Bỏng    | Trung bình | Bỏng độ 2, có phồng rộp      |
| 6   | burn_moderate_skintear | Bỏng    | Trung bình | Bỏng độ 2, rách da           |

---

### Q8: Tại sao EfficientNet dùng image size 224×224?

**Trả lời:**

- Đây là size chuẩn của **ImageNet** (pretrained weights)
- Phù hợp với **Transfer Learning**
- Nhỏ hơn giúp **inference nhanh hơn**

```python
# config.py
IMAGE_SIZE: int = 224
IMAGE_MEAN: List[float] = [0.485, 0.456, 0.406]  # ImageNet mean
IMAGE_STD: List[float] = [0.229, 0.224, 0.225]   # ImageNet std
```

---

## 4. Dataset & Training

### Q9: Dataset có bao nhiêu ảnh? Phân chia như thế nào?

**Trả lời:**

| Set        | Số ảnh    | Tỷ lệ    |
| ---------- | --------- | -------- |
| Training   | 1,583     | 70%      |
| Validation | 456       | 20%      |
| Test       | 230       | 10%      |
| **Tổng**   | **2,269** | **100%** |

---

### Q10: Phân bố các loại vết thương trong dataset như thế nào?

**Trả lời:**

| Loại        | Số ảnh | Tỷ lệ  |
| ----------- | ------ | ------ |
| Burn        | ~500   | 22.04% |
| Bruise      | ~500   | 22.04% |
| Abrasion    | ~500   | 22.04% |
| Normal_Skin | ~769   | 33.89% |

**Nhận xét:** Dataset khá cân bằng giữa 3 loại vết thương (~22% mỗi loại)

---

### Q11: Tại sao không thu thập ảnh từ bệnh viện thực tế mà phải dùng ảnh public?

**Trả lời:**

Vì ràng buộc **pháp lý và đạo đức**:

- Ảnh y tế là **dữ liệu nhạy cảm** (HIPAA)
- Cần **consent** từ bệnh nhân
- Quy trình xin phép mất **nhiều tháng**
- Dự án Capstone chỉ có **16 tuần**

---

### Q12: 2,269 ảnh có đủ để train model AI không?

**Trả lời:**

| Hệ thống           | Dataset size |
| ------------------ | ------------ |
| **SkinAid**        | 2,269 ảnh    |
| ImageNet           | 14 triệu ảnh |
| Google Dermatology | 100,000+ ảnh |

**Tại sao vẫn hoạt động được:**

- **Transfer Learning:** Tận dụng kiến thức từ ImageNet
- **Data Augmentation:** Tăng gấp 3-5x diversity
- **Task đơn giản hơn:** Chỉ 3 loại vết thương cơ bản

---

### Q13: Các kỹ thuật Data Augmentation được sử dụng là gì?

**Trả lời:**

| Technique  | Value                | Mục đích                    |
| ---------- | -------------------- | --------------------------- |
| Flip       | Horizontal, Vertical | Tăng đa dạng góc nhìn       |
| Crop       | 0-5% Zoom            | Mô phỏng khoảng cách chụp   |
| Rotation   | -10° đến +10°        | Mô phỏng góc xoay khi chụp  |
| Brightness | ±5%                  | Mô phỏng điều kiện ánh sáng |
| Blur       | Max 1px              | Mô phỏng ảnh mờ             |
| Noise      | Max 0.1%             | Tăng khả năng chống nhiễu   |

---

## 5. Các loại vết thương

### Q14: Tại sao chỉ có 3 loại vết thương (xước, bầm, bỏng)? Tại sao không thêm vết cắt?

**Trả lời:**

1. **Vết cắt nguy hiểm hơn** → cần đi bệnh viện ngay
2. **Khó phân loại severity** bằng ảnh (không thấy độ sâu)
3. **Scope dự án 16 tuần** → ưu tiên 3 loại phổ biến nhất
4. **Dataset vết cắt** khó tìm (thường không chụp ảnh khi chảy máu)

---

### Q15: Bỏng độ 3 (nặng) có được nhận diện không?

**Trả lời:** **KHÔNG**

Model chỉ có:

- `burn_mild` (độ 1)
- `burn_moderate_blister` (độ 2 - phồng rộp)
- `burn_moderate_skintear` (độ 2 - rách da)

**Lý do:** Bỏng độ 3 **phải đi bệnh viện ngay**, không cần AI suggest sơ cứu.

---

### Q16: Bỏng nước sôi và bỏng dầu mỡ khác nhau, model có phân biệt được không?

**Trả lời:** **KHÔNG**

Model chỉ phân loại theo **mức độ tổn thương bề mặt**, không phân biệt nguyên nhân:

- `burn_mild`: Da đỏ (bỏng độ 1)
- `burn_moderate_blister`: Có phồng rộp (bỏng độ 2)
- `burn_moderate_skintear`: Có rách da (bỏng độ 2)

---

### Q17: Vết bầm tím do bị đánh và vết bầm do va chạm có khác nhau không?

**Trả lời:**

**Model không phân biệt được nguyên nhân**, chỉ nhận diện **hình thái bề mặt**:

- Màu sắc vết bầm
- Diện tích vùng bầm
- Pattern màu sắc

---

## 6. Xử lý Edge Cases

### Q18: Nếu một người bị bỏng tay nhưng chụp ảnh trong phòng tối, hệ thống có nhận diện được không?

**Trả lời:**

Hệ thống **có thể gặp khó khăn** vì:

- YOLO yêu cầu ảnh rõ nét với vết thương trong khung hình
- Data augmentation chỉ điều chỉnh brightness ±5%, không xử lý ảnh quá tối

**Giải pháp đã có:**

- Thông báo yêu cầu: "Ảnh rõ nét, ánh sáng đủ"
- Nếu không phát hiện: trả về `total_detections: 0`

---

### Q19: Nếu một đứa trẻ bị xước đầu gối nhưng cũng có vết bầm bên cạnh, hệ thống xử lý như thế nào?

**Trả lời:**

Hệ thống **có thể detect nhiều vết thương** trong cùng 1 ảnh:

1. YOLO sẽ tạo **2 bounding boxes riêng biệt**
2. Mỗi crop sẽ được EfficientNet classify riêng
3. Response trả về `total_detections: 2` với 2 detections khác nhau

---

### Q20: Nếu người dùng upload ảnh không phải vết thương (ví dụ: nốt ruồi, mụn)?

**Trả lời:**

- YOLO detect 2 classes: `wound` và `non-wound`
- Nếu nhận là `non-wound`: trả về `primary_wound_type: "normal skin"`
- Nếu YOLO nhầm: EfficientNet có thể classify sai → đây là limitation

---

### Q21: Người có da ngăm và người da trắng, model có chính xác như nhau không?

**Trả lời:** **Có thể có bias** vì:

- Dataset từ nguồn công khai (Western-dominant)
- Thiếu diversity về ethnicity

> "Lack of diversity: The current dataset does not fully cover variations in ethnicity, age, and wound location on the body"

---

### Q22: Vết thương đang lành (đóng vảy) có được nhận diện không?

**Trả lời:** **Có thể không chính xác** vì:

- Training data chủ yếu là vết thương "fresh"
- Vết đóng vảy có morphology khác biệt
- Model có thể classify sai hoặc không detect

---

### Q23: Một người có hình xăm gần vết thương, model có bị nhầm không?

**Trả lời:** **Có thể bị ảnh hưởng** vì:

- YOLO có thể nhầm hình xăm là vết thương
- EfficientNet không được train với ảnh có hình xăm

**Giải pháp:** User nên chụp focus vào vết thương, tránh vùng có hình xăm

---

## 7. So sánh với hệ thống khác

### Q24: SkinAid khác gì với Google Lens khi chụp ảnh vết thương?

**Trả lời:**

| Tiêu chí               | SkinAid                    | Google Lens        |
| ---------------------- | -------------------------- | ------------------ |
| **Mục đích**           | Chuyên biệt cho vết thương | Nhận diện đa năng  |
| **Output**             | Loại + Severity + Sơ cứu   | Web search results |
| **Training data**      | Wound-specific             | General images     |
| **Accuracy cho wound** | Cao hơn (specialized)      | Thấp hơn (general) |

---

### Q25: So với app First Aid của Red Cross, SkinAid có gì khác biệt?

**Trả lời:**

| Tiêu chí           | SkinAid                   | Red Cross First Aid |
| ------------------ | ------------------------- | ------------------- |
| **AI Detection**   | ✅ Có                     | ❌ Không            |
| **Image Analysis** | ✅ Tự động                | ❌ User tự chọn     |
| **Personalized**   | ✅ Theo vết thương cụ thể | ❌ Hướng dẫn chung  |
| **Scope**          | 3 loại vết thương         | Nhiều tình huống    |

---

### Q26: Tại sao không dùng ChatGPT/GPT-4 Vision thay vì tự train model?

**Trả lời:**

| Tiêu chí      | GPT-4 Vision       | Custom Model      |
| ------------- | ------------------ | ----------------- |
| **Chi phí**   | $0.01-0.05/ảnh     | ~$0 (self-hosted) |
| **Control**   | Ít                 | Toàn quyền        |
| **Privacy**   | Gửi ảnh lên OpenAI | Giữ local         |
| **Customize** | Khó                | Dễ                |

→ **Custom model phù hợp hơn cho medical domain**

---

## 8. An toàn & Đạo đức

### Q27: AI có thể thay thế bác sĩ không?

**Trả lời:** **KHÔNG** - và đây là điểm quan trọng:

| Tiêu chí            | AI (SkinAid)      | Bác sĩ                           |
| ------------------- | ----------------- | -------------------------------- |
| Phạm vi             | 3 loại vết thương | Mọi loại                         |
| Context             | Chỉ xem ảnh       | Tiền sử, triệu chứng, xét nghiệm |
| Accuracy            | ~65%              | 90%+                             |
| Trách nhiệm pháp lý | Không             | Có                               |

**SkinAid chỉ là công cụ hỗ trợ sơ cứu ban đầu, không thay thế khám bệnh!**

---

### Q28: Nếu có vết thương nặng nhưng model nói "mild", hậu quả là gì?

**Trả lời:**

- **Rủi ro:** Người dùng delay đi bệnh viện
- **Giải pháp đã có:**
  - Model chỉ support 3 loại: abrasion, burn, bruise
  - Vết đứt sâu → có thể không detect hoặc misclassify
  - UI có warning rõ ràng

> "Classification errors can lead to inappropriate first aid guidance and potential legal liability"

---

### Q29: Hệ thống có lưu ảnh vết thương của người dùng không?

**Trả lời:**

- **Không lưu** sau khi xử lý xong
- Ảnh chỉ được load vào memory để inference
- Không có database lưu trữ hình ảnh người dùng

**Lý do:** Privacy concern trong medical domain

---

### Q30: Model của các bạn có ethical bias không?

**Trả lời:** **Có khả năng có bias** về:

- **Skin color:** Dataset chủ yếu Western
- **Age:** Có thể thiếu ảnh trẻ em, người già
- **Gender:** Không kiểm soát tỷ lệ

**Mitigation:** Disclaimer về limitations trong app

---

## 9. Hiệu năng & Deployment

### Q31: API endpoint chính là gì? Format request/response như thế nào?

**Trả lời:**

- **Endpoint:** `POST /analyze/`
- **Headers:** `X-API-Key` (xác thực)
- **Request:** Form-data với field `file` (ảnh JPEG/PNG, max 5MB)

**Response format:**

```json
{
  "success": true,
  "ai_model_version": "YOLOv11 and EfficientnetB0",
  "total_detections": 2,
  "processing_time_ms": 450,
  "primary_wound_type": "burn",
  "detections": [
    {
      "wound_type": "burn",
      "severity": "moderate_blister",
      "confidence_score": 0.89,
      "bbox": { "x": 120, "y": 80, "width": 230, "height": 200 }
    }
  ]
}
```

---

### Q32: Rate limiting được cấu hình như thế nào?

**Trả lời:**

- **Giới hạn:** 100 requests/ngày per IP

```python
# config.py
RATE_LIMIT: str = "100/day"
```

---

### Q33: Latency của hệ thống là bao nhiêu?

**Trả lời:**

- **Processing time:** ~200-500ms (AI inference)
- **Yêu cầu:** Response time ≤10 giây

**Cải thiện có thể:**

| Optimization              | Speed gain   |
| ------------------------- | ------------ |
| Model quantization (INT8) | 2-3x faster  |
| ONNX Runtime              | 1.5x faster  |
| GPU inference             | 5-10x faster |

---

### Q34: 100 người cùng upload ảnh lúc 8h sáng, hệ thống có crash không?

**Trả lời:**

- **Rate Limit:** 100 requests/day per IP → không phải global limit
- **Bottleneck:** CPU inference là sequential
- **Giải pháp nếu scale:**
  - Load balancer
  - Multiple server instances
  - Queue system

---

## 10. Tương lai & Phát triển

### Q35: Nếu muốn deploy lên mobile (offline), cần thay đổi gì?

**Trả lời:**

1. **Model Quantization:** Giảm size từ ~50MB → ~15MB
2. **Convert:** PyTorch → TensorFlow Lite / Core ML
3. **Trade-off:** Accuracy giảm ~2-5%
4. **Benefit:** Chạy offline, không cần internet

---

### Q36: Nếu có budget lớn, cải tiến đầu tiên nên làm là gì?

**Trả lời:**

**Thu thập thêm data chất lượng cao** vì:

- Data quyết định 80% chất lượng AI
- 2,269 ảnh vẫn còn ít
- Cần diverse hơn về ethnicity, age, wound location

**Ưu tiên 2:** Thêm GPU inference để giảm latency

---

### Q37: Tương lai có thể phát triển thêm gì?

**Trả lời:**

| Feature                | Mô tả                      | Độ khó     |
| ---------------------- | -------------------------- | ---------- |
| Thêm wound types       | Vết cắt, nhiễm trùng       | Cao        |
| Wound healing tracking | So sánh ảnh theo thời gian | Trung bình |
| Severity "severe"      | Thêm mức độ nặng           | Trung bình |
| Edge deployment        | Chạy offline trên mobile   | Cao        |
| Multi-language         | Hỗ trợ tiếng Việt          | Thấp       |

---

## 11. Câu hỏi "khó" từ Hội đồng

### Q38: Nếu có người chết vì làm theo hướng dẫn sai của AI, ai chịu trách nhiệm?

**Trả lời:**

- **Disclaimer rõ ràng:** "AI chỉ mang tính tham khảo"
- **Không thay thế bác sĩ** được ghi rõ
- **User đồng ý Terms of Service** trước khi dùng
- **Tương tự Google:** Tìm kiếm triệu chứng ≠ chẩn đoán

---

### Q39: Accuracy 65% có đủ tin cậy không?

**Trả lời:**

**So sánh với context:**

| Use case                 | Accuracy yêu cầu      |
| ------------------------ | --------------------- |
| Cancer diagnosis         | 95%+                  |
| Autonomous driving       | 99%+                  |
| **First-aid suggestion** | 60-70% chấp nhận được |

**Lý do 65% chấp nhận được:**

1. Đây là **tool hỗ trợ**, không thay thế bác sĩ
2. First-aid cho 3 loại vết thương cơ bản
3. Có warning rõ ràng: "Tham khảo ý kiến bác sĩ nếu nghiêm trọng"

---

### Q40: Phụ huynh muốn dùng app để check vết thương của con nhỏ trước khi đưa đi bệnh viện. App có phù hợp không?

**Trả lời:**

**Có thể phù hợp** cho:

- ✅ Xước nhẹ, bầm tím nhỏ, bỏng nhẹ → sơ cứu tại nhà

**Không phù hợp** cho:

- ❌ Vết cắt sâu, chảy máu nhiều, nghi gãy xương
- ❌ Thay thế việc đưa đến bác sĩ

---

### Q41: Một y tá ở trạm y tế xã muốn dùng hệ thống hỗ trợ phân loại bệnh nhân. Có nên không?

**Trả lời:**

**Có thể hỗ trợ** nhưng với điều kiện:

- Chỉ dùng như **công cụ tham khảo bổ sung**
- Y tá vẫn phải đánh giá bằng chuyên môn
- Không thay thế quy trình khám chính thức

**Lý do:** Accuracy 65% không đủ để làm tiêu chuẩn y tế

---

## 📌 Tóm tắt Key Points

| Chủ đề               | Số liệu quan trọng          |
| -------------------- | --------------------------- |
| Dataset              | 2,269 ảnh (70/20/10 split)  |
| YOLO classes         | 2 (wound, non-wound)        |
| EfficientNet classes | 7 (3 loại × 2-3 mức độ)     |
| Confidence threshold | 55%                         |
| Confidence fusion    | YOLO 30% + EfficientNet 70% |
| Target accuracy      | ≥65%                        |
| Response time        | ≤10 giây                    |
| Rate limit           | 100 requests/day            |

---

> **Chúc bạn thuyết trình thành công!** 🎓
