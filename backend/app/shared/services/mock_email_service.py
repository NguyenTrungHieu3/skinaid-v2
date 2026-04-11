import logging
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

class MockEmailService:
    def __init__(self):
        self.sent_emails = []

    def generate_verification_token(self) -> str:
        import uuid
        return f"mock_verification_token_{uuid.uuid4().hex[:8]}"

    async def send_verification_email(self, email: str, token: str) -> bool:
        email_data = {
            "type": "verification",
            "email": email,
            "token": token,
            "verification_link": f"{settings.BASE_URL}/verify-email?token={token}&email={email}"
        }
        logger.info(f"Mock: Sending verification email to {email} with token {token}")
        logger.info(f"Mock: Verification link: {settings.BASE_URL}/verify-email?token={token}&email={email}")
        self.sent_emails.append(email_data)
        return True

    async def send_verification_email_async(self, email: str, token: str) -> None:
        await self.send_verification_email(email, token)

    async def send_welcome_email(self, email: str, display_name: str) -> bool:
        email_data = {
            "type": "welcome",
            "email": email,
            "display_name": display_name
        }
        logger.info(f"Mock: Sending welcome email to {email} for {display_name}")
        self.sent_emails.append(email_data)
        return True

    async def send_password_reset_email(self, email: str, token: str) -> bool:
        email_data = {
            "type": "password_reset",
            "email": email,
            "token": token,
            "reset_link": f"{settings.BASE_URL}/reset-password?token={token}&email={email}"
        }
        logger.info(f"Mock: Sending password reset email to {email} with token {token}")
        logger.info(f"Mock: Reset link: {settings.BASE_URL}/reset-password?token={token}&email={email}")
        self.sent_emails.append(email_data)
        return True

    async def send_password_reset_email_async(self, email: str, token: str) -> None:
        await self.send_password_reset_email(email, token)

    async def send_welcome_email_async(self, email: str, display_name: str) -> None:
        email_data = {
            "type": "welcome",
            "email": email,
            "display_name": display_name
        }
        logger.info(f"Mock: Sending welcome email to {email} for {display_name}")
        self.sent_emails.append(email_data)

    async def send_password_changed_notification_async(self, email: str, display_name: str) -> None:
        email_data = {
            "type": "password_changed",
            "email": email,
            "display_name": display_name
        }
        logger.info(f"Mock: Sending password changed notification to {email}")
        self.sent_emails.append(email_data)

    async def send_password_reset_success_notification_async(self, email: str, display_name: str) -> None:
        email_data = {
            "type": "password_reset_success",
            "email": email,
            "display_name": display_name
        }
        logger.info(f"Mock: Sending password reset success notification to {email}")
        self.sent_emails.append(email_data)

    def get_sent_emails(self):
        return self.sent_emails

    def clear_sent_emails(self):
        self.sent_emails = []

mock_email_service = MockEmailService()