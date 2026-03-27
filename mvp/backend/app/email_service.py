"""
Email Service — SMTP with console fallback.

Uses SMTP if configured (SMTP_HOST set), otherwise logs email content to console.
This allows the auth flow to work in development without a real mail server.
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

logger = structlog.get_logger()


def _is_smtp_configured() -> bool:
    from app.config import settings
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _send_smtp(to_email: str, subject: str, html_body: str) -> None:
    from app.config import settings
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    if settings.SMTP_TLS:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
    else:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())


def _console_fallback(to_email: str, subject: str, link: str) -> None:
    logger.info(
        "email_console_fallback",
        to=to_email,
        subject=subject,
        link=link,
        note="Configure SMTP_HOST/SMTP_USER/SMTP_PASSWORD to send real emails",
    )
    print(f"\n{'='*60}")
    print(f"[EMAIL SIMULATION] To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Link: {link}")
    print(f"{'='*60}\n")


async def send_password_reset_email(to_email: str, token: str) -> None:
    """Send password reset email with token link."""
    from app.config import settings
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "Reset your SaaS-IA password"
    html_body = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#05C3DB">Reset your password</h2>
      <p>Click the link below to reset your password. This link expires in <strong>1 hour</strong>.</p>
      <a href="{link}" style="display:inline-block;padding:12px 24px;background:#05C3DB;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold">
        Reset Password
      </a>
      <p style="margin-top:16px;color:#666;font-size:0.85em">If you did not request this, ignore this email.</p>
      <p style="color:#666;font-size:0.75em">Link: {link}</p>
    </div>
    """
    if _is_smtp_configured():
        try:
            _send_smtp(to_email, subject, html_body)
            logger.info("password_reset_email_sent", to=to_email)
        except Exception as e:
            logger.warning("password_reset_email_failed", error=str(e))
            _console_fallback(to_email, subject, link)
    else:
        _console_fallback(to_email, subject, link)


async def send_verification_email(to_email: str, token: str) -> None:
    """Send email verification link."""
    from app.config import settings
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your SaaS-IA email address"
    html_body = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#05C3DB">Verify your email</h2>
      <p>Click the link below to verify your email address. This link expires in <strong>24 hours</strong>.</p>
      <a href="{link}" style="display:inline-block;padding:12px 24px;background:#05C3DB;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold">
        Verify Email
      </a>
      <p style="color:#666;font-size:0.75em">Link: {link}</p>
    </div>
    """
    if _is_smtp_configured():
        try:
            _send_smtp(to_email, subject, html_body)
            logger.info("verification_email_sent", to=to_email)
        except Exception as e:
            logger.warning("verification_email_failed", error=str(e))
            _console_fallback(to_email, subject, link)
    else:
        _console_fallback(to_email, subject, link)
