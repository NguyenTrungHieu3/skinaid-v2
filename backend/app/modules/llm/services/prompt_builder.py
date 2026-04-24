from __future__ import annotations

import logging
from typing import Final

from app.modules.llm.schemas.llm_schemas import RAGChunkSnapshot, SynthesisContext

logger = logging.getLogger(__name__)

# Token budget constants
_MAX_RAG_CHUNKS: Final[int] = 3          # tối đa 3 chunks RAG đưa vào prompt
_MAX_RAG_CHARS: Final[int] = 1_200       # tổng chars RAG context tối đa (giảm từ 2000)
_MAX_DB_STEP_CHARS: Final[int] = 1_000   # tổng chars DB guide tối đa (giảm từ 1500)

# Tên hiển thị thân thiện cho wound type
_WOUND_TYPE_DISPLAY: Final[dict[str, str]] = {
    "abrasion": "Trầy xước (Abrasion)",
    "bruise":   "Bầm tím (Bruise)",
    "burn":     "Bỏng (Burn)",
    "cut":      "Vết cắt / đứt (Cut)",
    "acne":     "Mụn trứng cá (Acne)",
    "fungal":   "Nấm da (Fungal infection)",
    "psoriasis":"Vảy nến (Psoriasis)",
}

_SEVERITY_DISPLAY: Final[dict[str, str]] = {
    "mild":     "Nhẹ (Mild)",
    "moderate": "Trung bình (Moderate)",
    "severe":   "Nặng (Severe)",
    "general":  "Tổng quát (General)",
}

_SUB_TYPE_DISPLAY: Final[dict[str, str]] = {
    "blister":  "Phồng rộp (Blister)",
    "skintear": "Rách da (Skin tear)",
}


class PromptBuilder:
    """Xây dựng system prompt và user prompt cho LLM synthesis — stateless."""

    def build_system_prompt(self) -> str:
        """System prompt định nghĩa vai trò, quy tắc ưu tiên, và yêu cầu output JSON."""
        return (
            "Bạn là trợ lý y tế sơ cứu của ứng dụng SkinAid. "
            "Nhiệm vụ của bạn là tổng hợp hướng dẫn sơ cứu dựa trên kết quả phân tích AI "
            "và thông tin người dùng cung cấp.\n\n"

            "QUY TẮC BẮT BUỘC:\n"
            "1. Luôn ưu tiên thông tin từ [HƯỚNG DẪN SƠ CỨU TỪ CƠ SỞ DỮ LIỆU] nếu được cung cấp.\n"
            "2. Dùng [KIẾN THỨC Y KHOA BỔ SUNG] để làm phong phú thêm, không được mâu thuẫn với hướng dẫn DB.\n"
            "3. Cá nhân hóa hướng dẫn dựa trên [MÔ TẢ CỦA NGƯỜI DÙNG] nếu có.\n"
            "4. Trả lời HOÀN TOÀN bằng tiếng Việt, rõ ràng, dễ hiểu.\n"
            "5. KHÔNG bịa đặt thông tin y tế không có trong context được cung cấp.\n"
            "6. Nếu tình trạng có vẻ nghiêm trọng, LUÔN khuyến nghị đến cơ sở y tế.\n\n"

            "ĐỊNH DẠNG OUTPUT BẮT BUỘC:\n"
            "Bạn PHẢI trả về một JSON object hợp lệ, KHÔNG có markdown, KHÔNG có giải thích thêm.\n"
            "JSON phải theo đúng schema sau:\n"
            "{\n"
            '  "title": "Tiêu đề hướng dẫn sơ cứu ngắn gọn",\n'
            '  "steps": ["Bước 1...", "Bước 2...", "Bước 3..."],\n'
            '  "dos": ["Nên làm 1...", "Nên làm 2..."],\n'
            '  "donts": ["Không nên làm 1...", "Không nên làm 2..."],\n'
            '  "supplies_needed": ["Vật tư 1...", "Vật tư 2..."],\n'
            '  "estimated_healing_time": "X-Y ngày"\n'
            "}\n\n"
            "Yêu cầu từng field:\n"
            "- title: chuỗi ngắn gọn mô tả loại vết thương và mức độ\n"
            "- steps: list 3-6 bước sơ cứu theo thứ tự, mỗi bước là một câu hoàn chỉnh\n"
            "- dos: list 2-4 điều nên làm\n"
            "- donts: list 2-4 điều không nên làm\n"
            "- supplies_needed: list vật tư/dụng cụ cần thiết\n"
            "- estimated_healing_time: thời gian hồi phục ước tính (ví dụ: '3-7 ngày')"
        )

    def build_user_prompt(self, context: SynthesisContext) -> str:
        """Tổng hợp user prompt từ AI result + DB guide + RAG chunks + user description."""
        sections: list[str] = []

        sections.append(self._build_ai_result_section(context))
        sections.append(self._build_db_guide_section(context))

        rag_section = self._build_rag_section(context.rag_chunks)
        if rag_section:
            sections.append(rag_section)

        if context.user_description and context.user_description.strip():
            sections.append(
                f"[MÔ TẢ CỦA NGƯỜI DÙNG]\n{context.user_description.strip()}"
            )

        sections.append(
            "Dựa trên tất cả thông tin trên, hãy trả về JSON hướng dẫn sơ cứu "
            "theo đúng schema đã quy định trong system prompt."
        )

        return "\n\n".join(sections)

    # Private section builders

    def _build_ai_result_section(self, context: SynthesisContext) -> str:
        wound_display = _WOUND_TYPE_DISPLAY.get(
            context.wound_type.lower(), context.wound_type
        )
        severity_display = _SEVERITY_DISPLAY.get(
            context.severity.lower(), context.severity
        )

        lines = [
            "[KẾT QUẢ PHÂN TÍCH AI]",
            f"- Loại tổn thương: {wound_display}",
            f"- Mức độ: {severity_display}",
        ]

        if context.sub_type:
            sub_display = _SUB_TYPE_DISPLAY.get(
                context.sub_type.lower(), context.sub_type
            )
            lines.append(f"- Phân loại phụ: {sub_display}")

        return "\n".join(lines)

    def _build_db_guide_section(self, context: SynthesisContext) -> str:
        if context.db_guide is None:
            return (
                "[HƯỚNG DẪN SƠ CỨU TỪ CƠ SỞ DỮ LIỆU]\n"
                "Không có hướng dẫn cụ thể trong cơ sở dữ liệu cho tình trạng này. "
                "Hãy sử dụng kiến thức y khoa bổ sung và mô tả của người dùng để đưa ra hướng dẫn phù hợp."
            )

        guide = context.db_guide
        lines = [f"[HƯỚNG DẪN SƠ CỨU TỪ CƠ SỞ DỮ LIỆU]\nTiêu đề: {guide.title}"]

        if guide.steps:
            steps_text = self._format_list("Các bước sơ cứu", guide.steps)
            lines.append(steps_text)

        if guide.dos:
            lines.append(self._format_list("Nên làm", guide.dos))

        if guide.donts:
            lines.append(self._format_list("Không nên làm", guide.donts))

        if guide.supplies_needed:
            lines.append(self._format_list("Vật tư cần thiết", guide.supplies_needed))

        if guide.estimated_healing_time:
            lines.append(f"Thời gian hồi phục ước tính: {guide.estimated_healing_time}")

        result = "\n".join(lines)

        if len(result) > _MAX_DB_STEP_CHARS:
            result = result[:_MAX_DB_STEP_CHARS] + "\n[... nội dung được rút gọn ...]"

        return result

    def _build_rag_section(self, chunks: list[RAGChunkSnapshot]) -> str:
        """Lấy top _MAX_RAG_CHUNKS chunks theo relevance_score, truncate về _MAX_RAG_CHARS."""
        if not chunks:
            return ""

        top_chunks = sorted(chunks, key=lambda c: c.relevance_score, reverse=True)
        top_chunks = top_chunks[:_MAX_RAG_CHUNKS]

        combined = "\n\n".join(
            f"[Nguồn {i + 1} — điểm liên quan: {c.relevance_score:.2f}]\n{c.content.strip()}"
            for i, c in enumerate(top_chunks)
        )

        if len(combined) > _MAX_RAG_CHARS:
            combined = combined[:_MAX_RAG_CHARS] + "\n[... nội dung được rút gọn ...]"
            logger.debug(
                "[PromptBuilder] RAG context truncated to %d chars.", _MAX_RAG_CHARS
            )

        return f"[KIẾN THỨC Y KHOA BỔ SUNG]\n{combined}"

    @staticmethod
    def _format_list(label: str, items: list[str]) -> str:
        """Format một danh sách thành bullet points có nhãn."""
        if not items:
            return ""
        bullet_lines = "\n".join(f"  • {item}" for item in items)
        return f"{label}:\n{bullet_lines}"
