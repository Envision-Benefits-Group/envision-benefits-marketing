# src/email/email_service.py
import os
import smtplib
import traceback
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from typing import List, Optional
from zoneinfo import ZoneInfo

import structlog
from dotenv import load_dotenv
from jinja2 import Environment, PackageLoader, select_autoescape

# load dotenv
load_dotenv()

# Initialize logger
logger = structlog.get_logger("EMAIL_SERVICE")


class EmailService:
    def __init__(self, module: str = None):
        # Check if using Mailpit for local development
        USE_MAILPIT = os.getenv("USE_MAILPIT", "False").lower() == "true"
        self.smtp_server = (
            "mailpit" if USE_MAILPIT else "email-smtp.us-west-2.amazonaws.com"
        )
        self.smtp_port = 1025 if USE_MAILPIT else 587

        # Handle credentials differently for Mailpit vs AWS SES
        if USE_MAILPIT:
            self.from_email = os.getenv("APP_EMAIL", "test@example.com")
            self.auth_email = os.getenv(
                "AUTH_EMAIL", "test@example.com"
            )  # For auth emails (signup, password reset)
            self.smtp_username = os.getenv("SMTP_USERNAME", "anything")
            self.smtp_password = os.getenv("SMTP_PASSWORD", "anything")
        else:
            self.from_email = os.getenv(
                "APP_EMAIL"
            )  # Sender email
            self.auth_email = os.getenv(
                "AUTH_EMAIL", "noreply@envisionhr.com"
            )  # For auth emails (signup, password reset)
            self.smtp_username = os.getenv("SMTP_USERNAME")  # SES SMTP user name
            self.smtp_password = os.getenv("SMTP_PASSWORD")  # SES SMTP password

            # Only validate credentials in production mode
            if not all([self.from_email, self.smtp_username, self.smtp_password]):
                logger.error(
                    "APP_EMAIL, SMTP_USERNAME, and SMTP_PASSWORD environment variables must be set"
                )
                raise ValueError(
                    "APP_EMAIL, SMTP_USERNAME, and SMTP_PASSWORD environment variables must be set"
                )

        self.module = module
        # Only set up Jinja environment if module is provided
        if module:
            self.env = Environment(
                loader=PackageLoader(self.module, "templates"),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.env = None
            logger.info("Initialized without templates (module not provided)")

        logger.info(
            "EmailService initialized",
            smtp_server=self.smtp_server,
            smtp_port=self.smtp_port,
        )

    def send_email(
        self,
        to_address: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        attachments=None,
    ):
        """
        Generic method to send an email with HTML and plain text content.

        Args:
            to_address: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (falls back to stripped HTML if not provided)
            attachments: List of attachment objects with {data, filename, subtype} keys

        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        try:
            logger.info(f"Preparing to send email to {to_address}")
            # Create message container
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_address
            msg["Subject"] = subject

            # If no plain text is provided, use a basic fallback
            if text_content is None:
                text_content = (
                    "Please view this email in an HTML-compatible email client."
                )

            # Attach parts
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Attach any files if provided
            if attachments:
                for attachment in attachments:
                    mime_attachment = MIMEApplication(
                        attachment["data"], _subtype=attachment["subtype"]
                    )
                    mime_attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=attachment["filename"],
                    )
                    msg.attach(mime_attachment)

            logger.info("Connecting to SMTP server...")
            # Connect and send email using SMTP credentials
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # For non-Mailpit servers, use TLS
                if self.smtp_port != 1025:  # Skip TLS for Mailpit
                    server.starttls()
                    # Only provide login credentials if they exist (needed for AWS SES)
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_address}")
            return True
        except Exception:
            tb_str = traceback.format_exc()
            logger.error(f"Error sending email to {to_address}", error=tb_str)
            return False

    def send_forgot_password_email(
        self, to_address: str, user_name: str, reset_link: str
    ):
        """
        Send an email containing a link the user can click to reset their password.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.auth_email  # Use auth email for password reset
            msg["To"] = to_address
            msg["Subject"] = "Reset Your Password"

            # Render templates
            html_template = self.env.get_template("forgot_password.html")
            txt_template = self.env.get_template("forgot_password.txt")

            html_content = html_template.render(
                user_name=user_name, reset_link=reset_link
            )
            txt_content = txt_template.render(
                user_name=user_name, reset_link=reset_link
            )

            msg.attach(MIMEText(txt_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # For non-Mailpit servers, use TLS
                if self.smtp_port != 1025:  # Skip TLS for Mailpit
                    server.starttls()
                    # Only provide login credentials if they exist
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Password reset email sent to {to_address}")
            return True
        except Exception:
            tb_str = traceback.format_exc()
            logger.error(
                f"Error sending forgot password email to {to_address}", error=tb_str
            )
            return False

    def send_test_email(self, to_address: str):
        """
        Send a test email to verify the email service is working correctly.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_address
            msg["Subject"] = "Test Email - Email Service Check"

            text_content = (
                "This is a test email to verify the email service is working correctly."
            )
            html_content = """
            <html>
              <body>
                <h2>Test Email</h2>
                <p>This is a test email to verify the email service is working correctly.</p>
                <p>If you received this email, the email service is configured and working properly.</p>
              </body>
            </html>
            """

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # For non-Mailpit servers, use TLS
                if self.smtp_port != 1025:  # Skip TLS for Mailpit
                    server.starttls()
                    # Only provide login credentials if they exist
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Test email sent successfully to {to_address}")
            return True
        except Exception:
            tb_str = traceback.format_exc()
            logger.error(f"Error sending test email to {to_address}", error=tb_str)
            return False

if __name__ == "__main__":
    try:
        # Initialize the email service without module for testing
        email_service = EmailService()

        # Send test email
        test_recipient = "hamzaadnan.work@gmail.com"
        success = email_service.send_test_email(test_recipient)

        if success:
            print(f"Test email sent successfully to {test_recipient}")
        else:
            print(f"Failed to send test email to {test_recipient}")
    except Exception as e:
        print(f"Error during testing: {str(e)}")
