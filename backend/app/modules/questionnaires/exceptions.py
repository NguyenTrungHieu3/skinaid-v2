from app.shared.exceptions.base import NotFoundError, BadRequestError


class QuestionnaireNotFoundError(NotFoundError):
    error_code: str = "QUESTIONNAIRE_NOT_FOUND"

    def __init__(self, questionnaire_id: str | None = None) -> None:
        message = (
            f"Không tìm thấy bộ câu hỏi {questionnaire_id}"
            if questionnaire_id
            else "Không tìm thấy bộ câu hỏi"
        )
        super().__init__(message=message)


class QuestionNotFoundError(NotFoundError):
    error_code: str = "QUESTION_NOT_FOUND"

    def __init__(self, question_id: str | None = None) -> None:
        message = (
            f"Không tìm thấy câu hỏi {question_id}"
            if question_id
            else "Không tìm thấy câu hỏi"
        )
        super().__init__(message=message)


class AnswerNotFoundError(NotFoundError):
    error_code: str = "ANSWER_NOT_FOUND"

    def __init__(self, answer_id: str | None = None) -> None:
        message = (
            f"Không tìm thấy đáp án {answer_id}"
            if answer_id
            else "Không tìm thấy đáp án"
        )
        super().__init__(message=message)


class ImportValidationError(BadRequestError):
    error_code: str = "IMPORT_VALIDATION_ERROR"

    def __init__(self, message: str = "Dữ liệu import không hợp lệ") -> None:
        super().__init__(message=message)


class ExportError(BadRequestError):
    error_code: str = "EXPORT_ERROR"

    def __init__(self, message: str = "Lỗi khi xuất dữ liệu") -> None:
        super().__init__(message=message)
