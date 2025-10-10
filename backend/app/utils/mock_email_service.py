"""
Mock email service for testing purposes
"""
import logging
import json

logger = logging.getLogger(__name__)

class MockEmailService:
    """Mock email service that doesn't actually send emails"""
    
    def __init__(self):
        self.sent_emails = []
    
    def generate_verification_token(self) -> str:
        import uuid
        return f"mock_verification_token_{uuid.uuid4().hex[:8]}"
    
    async def send_verification_email(self, email: str, token: str) -> bool:
        """Mock sending verification email"""
        email_data = {
            "type": "verification",
            "email": email,
            "token": token,
            "verification_link": f"http://localhost:3000/verify-email?token={token}&email={email}"
        }
        logger.info(f"Mock: Sending verification email to {email} with token {token}")
        logger.info(f"Mock: Verification link: http://localhost:3000/verify-email?token={token}&email={email}")
        self.sent_emails.append(email_data)
        return True
    
    async def send_welcome_email(self, email: str, display_name: str) -> bool:
        """Mock sending welcome email"""
        email_data = {
            "type": "welcome",
            "email": email,
            "display_name": display_name
        }
        logger.info(f"Mock: Sending welcome email to {email} for {display_name}")
        self.sent_emails.append(email_data)
        return True
    
    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Mock sending password reset email"""
        email_data = {
            "type": "password_reset",
            "email": email,
            "token": token,
            "reset_link": f"http://localhost:3000/reset-password?token={token}&email={email}"
        }
        logger.info(f"Mock: Sending password reset email to {email} with token {token}")
        logger.info(f"Mock: Reset link: http://localhost:3000/reset-password?token={token}&email={email}")
        self.sent_emails.append(email_data)
        return True
    
    def get_sent_emails(self):
        """Get list of sent emails for testing"""
        return self.sent_emails
    
    def clear_sent_emails(self):
        """Clear sent emails list"""
        self.sent_emails = []

mock_email_service = MockEmailService()