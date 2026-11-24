"""Transactional email over HTTPS; never expose a reset URL in API responses/logs."""
import json
import logging
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.config import get_settings
from app.lending_schemas import validate_email

logger = logging.getLogger(__name__)


def mail_ready():
    settings = get_settings()
    try:
        sender = validate_email(settings.mail_from_email)
        origin = urlsplit(settings.app_origin)
    except ValueError:
        return False
    return bool(settings.brevo_api_key.get_secret_value() and sender
                and origin.scheme == "https" and origin.hostname
                and not origin.username and not origin.password
                and not origin.query and not origin.fragment and origin.path in ("", "/"))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def send_password_reset(email: str, token: str):
    settings = get_settings()
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
