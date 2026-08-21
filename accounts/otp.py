"""Equivalent of src/utils/otp.js."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from django.conf import settings
import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_otp_sms(phone_number: str, otp_code: str):
    twilio_sid = os.getenv("TWILIO_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    # If Twilio keys are missing, print to console for local testing
    if not all([twilio_sid, twilio_token, from_number]):
        logger.info(f"[DEV MOCK SMS] Sending OTP {otp_code} to {phone_number}")
        print(f"\n============================\n[DEV SMS OTP] Phone: {phone_number} | Code: {otp_code}\n============================\n")
        return True

    try:
        client = Client(twilio_sid, twilio_token)
        client.messages.create(
            body=f"Your SadakSathi verification code is: {otp_code}",
            from_=from_number,
            to=phone_number
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS via Twilio: {str(e)}")
        return False


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def otp_expiry():
    return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_TTL_MINUTES)


def send_otp_sms(phone: str, code: str) -> None:
    """Replace with Twilio / MSG91 / your SMS provider of choice."""
    if settings.NODE_ENV != "production":
        print(f"[DEV] OTP for {phone}: {code}")
        return

    # Example with Twilio:
    # from twilio.rest import Client
    # client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
    # client.messages.create(
    #     to=phone,
    #     from_=settings.TWILIO_FROM_NUMBER,
    #     body=f"Your SadakSathi verification code is {code}. "
    #          f"It expires in {settings.OTP_TTL_MINUTES} minutes.",
    # )
    raise RuntimeError("SMS provider not configured")
