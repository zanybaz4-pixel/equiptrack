"""Transactional email over HTTPS; never expose a reset URL in API responses/logs."""
import json
import logging
import re
from hmac import digest
from secrets import token_urlsafe
from time import time
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.config import get_settings
from app.lending_schemas import validate_email

logger = logging.getLogger(__name__)
GMAIL_SCRIPT = re.compile(r"https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec")


def mail_ready():
    settings = get_settings()
    try:
        origin = urlsplit(settings.app_origin)
    except ValueError:
        return False
    if not (origin.scheme == "https" and origin.hostname and not origin.username
            and not origin.password and not origin.query and not origin.fragment
            and origin.path in ("", "/")):
        return False
    if settings.recovery_mail_provider == "gmail":
        return bool(GMAIL_SCRIPT.fullmatch(settings.gmail_script_url)
                    and len(settings.gmail_relay_secret.get_secret_value()) >= 32)
    if settings.recovery_mail_provider != "brevo":
        return False
    try:
        sender = validate_email(settings.mail_from_email)
    except ValueError:
        return False
    return bool(settings.brevo_api_key.get_secret_value() and sender)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GoogleResponseRedirect(HTTPRedirectHandler):
    """Apps Script redirects only the response to Google's content host."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if (code not in (302, 303) or target.scheme != "https"
                or target.hostname != "script.googleusercontent.com"
                or target.username or target.password or target.port not in (None, 443)):
            return None
        # Only retrieve the response. Never forward the signed request body.
        return Request(newurl, headers={"Accept": "application/json"}, method="GET")


def send_gmail_reset(settings, email, token):
    if not GMAIL_SCRIPT.fullmatch(settings.gmail_script_url):
        raise ValueError("Invalid Gmail relay endpoint")
    payload = {"issued_at": int(time()), "request_id": token_urlsafe(16), "email": email, "token": token}
    message = "\n".join(str(payload[key]) for key in ("issued_at", "request_id", "email", "token"))
    payload["signature"] = digest(settings.gmail_relay_secret.get_secret_value().encode(),
                                  message.encode(), "sha256").hex()
    request = Request(settings.gmail_script_url, method="POST", data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json", "Accept": "application/json"})
    with build_opener(GoogleResponseRedirect()).open(request, timeout=12) as response:
        if response.status != 200 or json.loads(response.read(2048)).get("ok") is not True:
            raise RuntimeError("Gmail relay did not accept the message")


def send_password_reset(email: str, token: str):
    settings = get_settings()
    if settings.recovery_mail_provider == "gmail":
        try:
            send_gmail_reset(settings, email, token)
        except Exception as failure:
            logger.error("password_reset_delivery_failed type=%s", type(failure).__name__)
        return
    # The fragment is not sent in HTTP requests or Referer headers.
    link = settings.app_origin.rstrip("/") + "/#/reset-password?" + urlencode({"token": token})
    payload = {
        "sender": {"name": "EquipTrack", "email": settings.mail_from_email},
        "to": [{"email": email}],
        "subject": "Reset your EquipTrack password",
        "textContent": (
            "We received a request to reset your EquipTrack password.\n\n"
            f"Choose a new password here:\n{link}\n\n"
            "This link expires in 15 minutes and can be used once. "
            "After resetting, sign in again on your devices.\n\n"
            "If you did not request this, ignore this email. Your password has not changed.\n"
            "Use a separate EquipTrack password, not your Gmail password."
        ),
        "tags": ["password-reset"],
    }
    request = Request("https://api.brevo.com/v3/smtp/email", method="POST",
                      data=json.dumps(payload).encode("utf-8"), headers={
                          "Content-Type": "application/json", "Accept": "application/json",
                          "api-key": settings.brevo_api_key.get_secret_value(),
                      })
    try:
        with build_opener(NoRedirect()).open(request, timeout=8) as response:
            if response.status != 201:
                raise RuntimeError("Email provider did not accept the message")
    except Exception as failure:
        # Provider exception bodies can contain credentials, email addresses and links.
        logger.error("password_reset_delivery_failed type=%s", type(failure).__name__)
