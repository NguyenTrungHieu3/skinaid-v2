import os

def run_startup_checks():
    print("\nEmail Configuration:")
    check_email_config()
    print()


def check_email_config():
    try:
        use_mock = os.getenv("TESTING") == "true" or os.getenv("USE_MOCK_EMAIL") == "true"

        if use_mock:
            print(" Using MOCK email service (testing mode)")
            return

        from app.shared.services.email_service import email_service

        print(f"   SMTP Server: {email_service.smtp_server}")
        print(f"   SMTP Port: {email_service.smtp_port}")
        print(f"   Sender: {email_service.sender_email}")
        print(f"   Password: {'Configured' if email_service.sender_password else 'Not configured'}")

        test_smtp_connection(email_service)

    except ImportError:
        print(" Email service not available")
    except Exception as e:
        print(f"Email error: {str(e)}")


def test_smtp_connection(email_service):
    try:
        import smtplib

        print("Testing SMTP connection...")
        with smtplib.SMTP(
            email_service.smtp_server,
            email_service.smtp_port,
            timeout=10
        ) as server:
            server.starttls()
            print("SMTP connection successful")

    except Exception as e:
        print(f"SMTP connection failed: {str(e)}")