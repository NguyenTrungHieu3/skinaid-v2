import smtplib
import secrets
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta
import logging
import os
from urllib.parse import quote, quote_plus

# Import settings to get SMTP configuration
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Load email configuration from settings
        self.smtp_server = getattr(settings, 'SMTP_SERVER', os.getenv("SMTP_SERVER", "smtp.gmail.com"))
        self.smtp_port = int(getattr(settings, 'SMTP_PORT', os.getenv("SMTP_PORT", "587")))
        self.sender_email = getattr(settings, 'SMTP_USERNAME', os.getenv("SMTP_USERNAME", "your-app-email@gmail.com")) 
        self.sender_password = getattr(settings, 'SMTP_PASSWORD', os.getenv("SMTP_PASSWORD", "your-app-password"))
        
    def generate_verification_token(self) -> str:
        return secrets.token_urlsafe(32)
    
    def create_verification_email_content(self, email: str, token: str) -> tuple[str, str, str]:
        subject = "SkinAid - Xác thực tài khoản của bạn"
        
        # URL encode email and token to handle special characters
        encoded_email = quote_plus(email)
        encoded_token = quote_plus(token)
        
        verification_url = f"http://localhost:3000/verify-email?token={encoded_token}&email={encoded_email}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Xác thực tài khoản SkinAid</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50;">🩹 SkinAid</h1>
                    <h2 style="color: #666;">Xác thực tài khoản của bạn</h2>
                </div>
                
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p>Xin chào,</p>
                    <p>Cảm ơn bạn đã đăng ký tài khoản SkinAid! Để hoàn tất quá trình đăng ký, vui lòng xác thực địa chỉ email của bạn.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Xác thực Email
                        </a>
                    </div>
                    
                    <p>Hoặc copy và paste link sau vào trình duyệt:</p>
                    <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 5px;">
                        {verification_url}
                    </p>
                    
                    <p><strong>Lưu ý:</strong> Link xác thực này sẽ hết hạn sau 24 giờ.</p>
                    <p><strong>Debug Info:</strong> Email: {email}, Token: {token[:20]}...</p>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 12px;">
                    <p>Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.</p>
                    <p>© 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
        SkinAid - Xác thực tài khoản của bạn
        
        Xin chào,
        
        Cảm ơn bạn đã đăng ký tài khoản SkinAid! Để hoàn tất quá trình đăng ký, vui lòng xác thực địa chỉ email của bạn.
        
        Vui lòng truy cập link sau để xác thực:
        {verification_url}
        
        Lưu ý: Link xác thực này sẽ hết hạn sau 24 giờ.
        
        Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.
        
        Debug Info: Email: {email}, Token: {token[:20]}...
        
        © 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh
        """
        
        return subject, html_body, text_body
    
    def create_password_reset_email_content(self, email: str, token: str) -> tuple[str, str, str]:
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
                        <a href="http://localhost:3000/reset-password?token={token}&email={email}" 
                           style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Đặt lại mật khẩu
                        </a>
                    </div>
                    
                    <p>Hoặc copy và paste link sau vào trình duyệt:</p>
                    <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 5px;">
                        http://localhost:3000/reset-password?token={token}&email={email}
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
        
        # Plain text version
        text_body = f"""
        SkinAid - Đặt lại mật khẩu của bạn
        
        Xin chào,
        
        Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản SkinAid của bạn.
        
        Vui lòng truy cập link sau để đặt lại mật khẩu:
        http://localhost:3000/reset-password?token={token}&email={email}
        
        Lưu ý: Link đặt lại mật khẩu này sẽ hết hạn sau 1 giờ.
        
        Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này. Mật khẩu hiện tại của bạn sẽ không bị thay đổi.
        
        © 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh
        """
        
        return subject, html_body, text_body
    
    async def send_verification_email(self, email: str, token: str) -> bool:
        try:
            subject, html_body, text_body = self.create_verification_email_content(email, token)
            
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
            
            logger.info(f"Verification email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False
    
    async def send_welcome_email(self, email: str, display_name: str) -> bool:
        """Send welcome email after successful verification"""
        try:
            subject = "Chào mừng bạn đến với SkinAid! 🎉"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Chào mừng đến với SkinAid</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4CAF50;">🩹 SkinAid</h1>
                        <h2 style="color: #666;">Chào mừng bạn!</h2>
                    </div>
                    
                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px;">
                        <p>Xin chào <strong>{display_name}</strong>,</p>
                        <p>Chúc mừng! Tài khoản của bạn đã được xác thực thành công. Bạn có thể bắt đầu sử dụng SkinAid ngay bây giờ.</p>
                        
                        <h3 style="color: #4CAF50;">Tính năng chính của SkinAid:</h3>
                        <ul>
                            <li>🔍 Phân tích và nhận diện vết thương bằng AI</li>
                            <li>📋 Đánh giá mức độ nghiêm trọng</li>
                            <li>💡 Đưa ra khuyến nghị sơ cứu phù hợp</li>
                            <li>📊 Theo dõi quá trình hồi phục</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:3000/signin" 
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Đăng nhập ngay
                            </a>
                        </div>
                    </div>
                    
                    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
                        <p>© 2024 SkinAid - Hệ thống chăm sóc vết thương thông minh</p>
                    </div>
                </div>
            </body>
            </html>
            """
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = email
            
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"Welcome email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            return False
    
    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email"""
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

email_service = EmailService()