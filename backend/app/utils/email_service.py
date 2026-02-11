import smtplib
import secrets
import uuid
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta
import logging
import os
from urllib.parse import quote, quote_plus

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', os.getenv("SMTP_SERVER", "smtp.gmail.com"))
        self.smtp_port = int(getattr(settings, 'SMTP_PORT', os.getenv("SMTP_PORT", "587")))
        self.sender_email = getattr(settings, 'SMTP_USERNAME', os.getenv("SMTP_USERNAME", "your-app-email@gmail.com")) 
        self.sender_password = getattr(settings, 'SMTP_PASSWORD', os.getenv("SMTP_PASSWORD", "your-app-password"))
        
    def generate_verification_token(self) -> str:
        return secrets.token_urlsafe(32)
    
    def create_password_reset_email_content(self, email: str, token: str) -> tuple[str, str, str]:
        encoded_token = quote(token)
        encoded_email = quote(email)
        subject = "SkinAid - Đặt lại mật khẩu của bạn"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Đặt lại mật khẩu SkinAid</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50;">🩹 SkinAid</h1>
                    <h2 style="color: #666;">Đặt lại mật khẩu của bạn</h2>
                </div>
                
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p>Xin chào,</p>
                    <p>Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản SkinAid của bạn.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:5173/reset-password?token={encoded_token}&email={encoded_email}"
                           style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Đặt lại mật khẩu
                        </a>
                    </div>

                    <p>Hoặc copy và paste link sau vào trình duyệt:</p>
                    <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 5px;">
                        http://localhost:5173/reset-password?token={encoded_token}&email={encoded_email}
                    </p>
                    
                    <p><strong>Lưu ý:</strong> Link đặt lại mật khẩu này sẽ hết hạn sau 1 giờ.</p>
                    <p>Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này. Mật khẩu hiện tại của bạn sẽ không bị thay đổi.</p>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 12px;">
                    <p>© 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        SkinAid - Đặt lại mật khẩu của bạn

        Xin chào,

        Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản SkinAid của bạn.

        Vui lòng truy cập link sau để đặt lại mật khẩu:
        http://localhost:5173/reset-password?token={encoded_token}&email={encoded_email}

        Lưu ý: Link đặt lại mật khẩu này sẽ hết hạn sau 1 giờ.

        Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này. Mật khẩu hiện tại của bạn sẽ không bị thay đổi.

        © 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh
        """
        
        return subject, html_body, text_body

    def _send_email_sync(self, email: str, token: str, email_type: str):
        """Synchronous email sending executed in thread pool"""
        try:
            if email_type == "password_reset":
                subject, html_body, text_body = self.create_password_reset_email_content(email, token)
            else:
                raise ValueError(f"Unknown email type: {email_type}")

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = email

            text_part = MIMEText(text_body, "plain", "utf-8")
            html_part = MIMEText(html_body, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"{email_type.title()} email sent successfully to {email}")

        except Exception as e:
            logger.error(f"Failed to send {email_type} email to {email}: {str(e)}")
            raise
     
    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email synchronously (legacy method)"""
        try:
            subject, html_body, text_body = self.create_password_reset_email_content(email, token)

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = email

            text_part = MIMEText(text_body, "plain", "utf-8")
            html_part = MIMEText(html_body, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Password reset email sent successfully to {email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False

    async def send_password_reset_email_async(self, email: str, token: str) -> None:
        """Send password reset email asynchronously using thread pool"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_email_sync,
                email,
                token,
                "password_reset"
            )
            logger.info(f"Password reset email queued for {email}")
        except Exception as e:
            logger.error(f"Failed to queue password reset email for {email}: {str(e)}")
            raise

    async def send_password_changed_notification(self, email: str, display_name: str) -> bool:
        """Send password changed notification email synchronously (legacy method)"""
        try:
            subject = "SkinAid - Mật khẩu đã được thay đổi"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Mật khẩu đã được thay đổi - SkinAid</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4CAF50;">🩹 SkinAid</h1>
                        <h2 style="color: #666;">Mật khẩu đã được thay đổi</h2>
                    </div>

                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px;">
                        <p>Xin chào <strong>{display_name}</strong>,</p>
                        <p>Chúng tôi muốn thông báo rằng mật khẩu tài khoản SkinAid của bạn đã được thay đổi thành công.</p>

                        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Thời gian thay đổi:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                        </div>

                        <p><strong>Nếu bạn không thực hiện thay đổi này:</strong></p>
                        <ul>
                            <li>Vui lòng liên hệ ngay với chúng tôi</li>
                            <li>Đổi mật khẩu để bảo vệ tài khoản</li>
                            <li>Kiểm tra các hoạt động đăng nhập gần đây</li>
                        </ul>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:3000/signin"
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Đăng nhập tài khoản
                            </a>
                        </div>
                    </div>

                    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
                        <p>Nếu bạn có câu hỏi, vui lòng liên hệ với đội ngũ hỗ trợ của chúng tôi.</p>
                        <p>© 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            SkinAid - Mật khẩu đã được thay đổi

            Xin chào {display_name},

            Chúng tôi muốn thông báo rằng mật khẩu tài khoản SkinAid của bạn đã được thay đổi thành công.

            Thời gian thay đổi: {datetime.now().strftime('%d/%m/%Y %H:%M')}

            Nếu bạn không thực hiện thay đổi này:
            - Vui lòng liên hệ ngay với chúng tôi
            - Đổi mật khẩu để bảo vệ tài khoản
            - Kiểm tra các hoạt động đăng nhập gần đây

            Nếu bạn có câu hỏi, vui lòng liên hệ với đội ngũ hỗ trợ của chúng tôi.

            © 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh
            """

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = email

            text_part = MIMEText(text_body, "plain", "utf-8")
            html_part = MIMEText(html_body, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Password changed notification email sent successfully to {email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password changed notification email to {email}: {str(e)}")
            return False

    async def send_password_changed_notification_async(self, email: str, display_name: str) -> None:
        """Send password changed notification email asynchronously using thread pool"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_password_changed_notification_sync,
                email,
                display_name
            )
            logger.info(f"Password changed notification email queued for {email}")
        except Exception as e:
            logger.error(f"Failed to queue password changed notification email for {email}: {str(e)}")
            raise

    def _send_password_changed_notification_sync(self, email: str, display_name: str):
        """Synchronous password changed notification email sending executed in thread pool"""
        try:
            subject = "SkinAid - Mật khẩu đã được thay đổi"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Mật khẩu đã được thay đổi - SkinAid</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4CAF50;">🩹 SkinAid</h1>
                        <h2 style="color: #666;">Mật khẩu đã được thay đổi</h2>
                    </div>

                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px;">
                        <p>Xin chào <strong>{display_name}</strong>,</p>
                        <p>Chúng tôi muốn thông báo rằng mật khẩu tài khoản SkinAid của bạn đã được thay đổi thành công.</p>

                        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Thời gian thay đổi:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                        </div>

                        <p><strong>Nếu bạn không thực hiện thay đổi này:</strong></p>
                        <ul>
                            <li>Vui lòng liên hệ ngay với chúng tôi</li>
                            <li>Đổi mật khẩu để bảo vệ tài khoản</li>
                            <li>Kiểm tra các hoạt động đăng nhập gần đây</li>
                        </ul>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:3000/signin"
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Đăng nhập tài khoản
                            </a>
                        </div>
                    </div>

                    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
                        <p>Nếu bạn có câu hỏi, vui lòng liên hệ với đội ngũ hỗ trợ của chúng tôi.</p>
                        <p>© 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            SkinAid - Mật khẩu đã được thay đổi

            Xin chào {display_name},

            Chúng tôi muốn thông báo rằng mật khẩu tài khoản SkinAid của bạn đã được thay đổi thành công.

            Thời gian thay đổi: {datetime.now().strftime('%d/%m/%Y %H:%M')}

            Nếu bạn không thực hiện thay đổi này:
            - Vui lòng liên hệ ngay với chúng tôi
            - Đổi mật khẩu để bảo vệ tài khoản
            - Kiểm tra các hoạt động đăng nhập gần đây

            Nếu bạn có câu hỏi, vui lòng liên hệ với đội ngũ hỗ trợ của chúng tôi.

            © 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh
            """

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = email

            text_part = MIMEText(text_body, "plain", "utf-8")
            html_part = MIMEText(html_body, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Password changed notification email sent successfully to {email}")

        except Exception as e:
            logger.error(f"Failed to send password changed notification email to {email}: {str(e)}")
            raise

email_service = EmailService()