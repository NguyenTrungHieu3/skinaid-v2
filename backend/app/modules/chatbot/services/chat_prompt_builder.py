from __future__ import annotations

import logging
from typing import Any, Final

from app.modules.chatbot.schemas.chat_schemas import MessageItem

logger = logging.getLogger(__name__)

_WOUND_TYPE_DISPLAY: Final[dict[str, str]] = {
    "abrasion": "Trầy xước (Abrasion)",
    "bruise": "Bầm tím (Bruise)",
    "burn": "Bỏng (Burn)",
    "cut": "Vết cắt / đứt (Cut)",
    "acne": "Mụn trứng cá (Acne)",
    "fungal": "Nấm da (Fungal infection)",
    "psoriasis": "Vảy nến (Psoriasis)",
}

_SEVERITY_DISPLAY: Final[dict[str, str]] = {
    "mild": "Nhẹ (Mild)",
    "moderate": "Trung bình (Moderate)",
    "severe": "Nặng (Severe)",
}

_SUB_TYPE_DISPLAY: Final[dict[str, str]] = {
    "blister": "Phồng rộp (Blister)",
    "skintear": "Rách da (Skin tear)",
}

_MAX_RAG_CHUNKS: Final[int] = 3
_MAX_RAG_CHARS: Final[int] = 1_200
_MAX_FIRSTAID_CHARS: Final[int] = 1_000


class ChatPromptBuilder:
    """Stateless prompt builder cho 2 mode chatbot: Wound Advisor và App Guide."""

    def build_wound_advisor_prompt(
        self,
        wound_type: str,
        severity: str,
        sub_type: str | None,
        firstaid_snapshot: dict[str, Any] | None,
        rag_chunks: list[Any] | None = None,
    ) -> str:
        """Build system prompt cho Wound Advisor — STRICT scope chỉ wound đã quét."""
        wt_display = _WOUND_TYPE_DISPLAY.get(wound_type.lower(), wound_type)
        sev_display = _SEVERITY_DISPLAY.get(severity.lower(), severity)

        lines: list[str] = [
            "Bạn là trợ lý y tế của ứng dụng SkinAid.",
            "",
            "Bạn ĐANG hỗ trợ người dùng về một vết thương CỤ THỂ đã được phân tích bằng AI:",
            "",
            "[KẾT QUẢ PHÂN TÍCH]",
            f"- Loại vết thương: {wt_display}",
            f"- Mức độ nghiêm trọng: {sev_display}",
        ]

        if sub_type:
            st_display = _SUB_TYPE_DISPLAY.get(sub_type.lower(), sub_type)
            lines.append(f"- Phân loại phụ: {st_display}")

        # Firstaid section
        lines.append("")
        lines.append("[HƯỚNG DẪN SƠ CỨU TỪ CƠ SỞ DỮ LIỆU]")
        if firstaid_snapshot:
            lines.append(self._format_firstaid_snapshot(firstaid_snapshot))
        else:
            lines.append("Không có hướng dẫn cụ thể trong cơ sở dữ liệu.")

        # RAG section
        lines.append("")
        rag_text = self._format_rag_chunks(rag_chunks)
        if rag_text:
            lines.append("[KIẾN THỨC Y KHOA BỔ SUNG]")
            lines.append(rag_text)
        else:
            lines.append("[KIẾN THỨC Y KHOA BỔ SUNG]")
            lines.append("Không có kiến thức bổ sung.")

        # Strict rules
        lines.extend([
            "",
            "═══════════════════════════════════════",
            "QUY TẮC BẮT BUỘC — VI PHẠM = LỖI NGHIÊM TRỌNG:",
            "",
            f"1. CHỈ trả lời câu hỏi liên quan đến {wt_display} mức độ {sev_display}.",
            "",
            "2. Nếu người dùng hỏi về LOẠI VẾT THƯƠNG KHÁC, BẮT BUỘC trả lời:",
            f'   "Tôi đang hỗ trợ bạn về {wt_display} ({sev_display}). '
            f'Để được tư vấn về vết thương khác, vui lòng quay lại và chụp ảnh phân tích vết thương đó."',
            "",
            "3. Nếu người dùng hỏi CHỦ ĐỀ NGOÀI y tế / sơ cứu, BẮT BUỘC trả lời:",
            f'   "Tôi chỉ có thể hỗ trợ về vết thương đã được phân tích ({wt_display}). '
            f'Vui lòng đặt câu hỏi liên quan đến vết thương này."',
            "",
            "4. DỰA TRÊN thông tin sơ cứu từ cơ sở dữ liệu và kiến thức y khoa bổ sung ở trên.",
            "   KHÔNG bịa đặt thông tin y tế không có trong context.",
            "",
            "5. Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu, thân thiện.",
            "",
            "6. Nếu tình trạng có dấu hiệu nghiêm trọng (nhiễm trùng, không cải thiện sau 48h,",
            "   mức độ nặng), LUÔN khuyến nghị đến cơ sở y tế.",
            "",
            "7. KHÔNG đưa ra chẩn đoán chính thức — đây chỉ là hướng dẫn sơ cứu ban đầu.",
            "═══════════════════════════════════════",
        ])

        return "\n".join(lines)

    def build_app_guide_prompt(self) -> str:
        """Build system prompt cho App Guide — hướng dẫn sử dụng SkinAid."""
        return (
            "Bạn là trợ lý hướng dẫn sử dụng ứng dụng SkinAid — ứng dụng sơ cứu vết thương bằng AI.\n"
            "\n"
            "TÍNH NĂNG CỦA SKINAID:\n"
            "1. Chụp/Upload ảnh vết thương → AI tự động phân tích loại vết thương, mức độ nghiêm trọng, "
            "và đưa ra hướng dẫn sơ cứu\n"
            "2. Xem kết quả phân tích chi tiết: loại vết thương (bỏng, trầy xước, bầm tím, vết cắt, "
            "mụn, nấm da, vảy nến), mức độ (nhẹ/trung bình/nặng), các bước sơ cứu cụ thể\n"
            "3. Chat với AI về vết thương đã phân tích (chỉ khả dụng sau khi có kết quả phân tích ảnh)\n"
            "4. Xem lịch sử các lần phân tích trước đó\n"
            "5. Tìm bệnh viện, phòng khám, nhà thuốc gần vị trí hiện tại\n"
            "6. Quản lý tài khoản và hồ sơ cá nhân\n"
            "\n"
            "CÁCH SỬ DỤNG:\n"
            "- Bước 1: Đăng ký / Đăng nhập tài khoản\n"
            "- Bước 2: Chụp hoặc upload ảnh vết thương\n"
            "- Bước 3: Chờ AI phân tích (vài giây)\n"
            "- Bước 4: Xem kết quả + hướng dẫn sơ cứu\n"
            "- Bước 5: (Tùy chọn) Chat thêm với AI về vết thương đó\n"
            "- Bước 6: (Tùy chọn) Tìm bệnh viện gần nhất nếu cần\n"
            "\n"
            "QUY TẮC:\n"
            "1. Trả lời bằng tiếng Việt, thân thiện, dễ hiểu\n"
            "2. CHỈ trả lời về cách sử dụng ứng dụng SkinAid và các tính năng của nó\n"
            "3. Nếu người dùng hỏi về Y TẾ / SƠ CỨU cụ thể → hướng dẫn họ dùng tính năng chụp ảnh phân tích\n"
            "4. Nếu người dùng hỏi chủ đề HOÀN TOÀN NGOÀI app → từ chối nhẹ nhàng:\n"
            '   "Tôi là trợ lý hướng dẫn sử dụng SkinAid. Bạn có câu hỏi nào về cách dùng app không?"\n'
            "5. Khuyến khích người dùng khám phá các tính năng của app"
        )


    def build_messages(
        self,
        system_prompt: str,
        history: list[MessageItem],
        current_message: str,
    ) -> list[dict[str, str]]:
        """Assemble messages list cho OpenAI API: [system, ...history, user_msg]."""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        for item in history:
            messages.append({
                "role": item.role,
                "content": item.content,
            })

        messages.append({"role": "user", "content": current_message})
        return messages


    def _format_firstaid_snapshot(self, snapshot: dict[str, Any]) -> str:
        """Format firstaid_snapshot dict thành text cho prompt."""
        parts: list[str] = []

        title = snapshot.get("title", "")
        if title:
            parts.append(f"Tiêu đề: {title}")

        for label, key in [
            ("Các bước sơ cứu", "steps"),
            ("Nên làm", "dos"),
            ("Không nên làm", "donts"),
            ("Vật tư cần thiết", "supplies_needed"),
        ]:
            items = snapshot.get(key, [])
            if items:
                bullets = "\n".join(f"  - {item}" for item in items)
                parts.append(f"{label}:\n{bullets}")

        healing = snapshot.get("estimated_healing_time")
        if healing:
            parts.append(f"Thời gian hồi phục ước tính: {healing}")

        text = "\n".join(parts)
        if len(text) > _MAX_FIRSTAID_CHARS:
            text = text[:_MAX_FIRSTAID_CHARS] + "\n[... nội dung được rút gọn ...]"
        return text

    def _format_rag_chunks(self, chunks: list[Any] | None) -> str:
        """Format RAG chunks thành text cho prompt. Nhận RetrievedChunk objects."""
        if not chunks:
            return ""

        top = sorted(chunks, key=lambda c: c.score, reverse=True)[:_MAX_RAG_CHUNKS]

        parts = []
        for i, chunk in enumerate(top):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            parts.append(f"[Nguồn {i + 1} — điểm liên quan: {chunk.score:.2f}]\n{content.strip()}")

        combined = "\n\n".join(parts)
        if len(combined) > _MAX_RAG_CHARS:
            combined = combined[:_MAX_RAG_CHARS] + "\n[... nội dung được rút gọn ...]"
        return combined
