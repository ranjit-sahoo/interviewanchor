"""Transactional verification mail via Brevo HTTPS or an existing SMTP relay.

Brevo works on free Render instances, which block standard SMTP ports.
Set BREVO_API_KEY and SMTP_FROM='InterviewAnchor <verified@example.com>'.
The sender must be verified in Brevo. No marketing contacts are uploaded.
Without either provider configured, address ownership stays unverified.
"""
import http.client
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr

HOST = os.environ.get("SMTP_HOST", "")
PORT = int(os.environ.get("SMTP_PORT", "587"))
USER = os.environ.get("SMTP_USER", "")
PASSWORD = os.environ.get("SMTP_PASS", "")
FROM = os.environ.get("SMTP_FROM", USER or "noreply@localhost")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")


def enabled() -> bool:
    return bool(BREVO_API_KEY or HOST)


def send(to: str, subject: str, text: str) -> None:
    if not enabled():
        raise RuntimeError("mail not configured")
    # EmailMessage validates header line breaks for both delivery paths.
    msg = EmailMessage()
    msg["From"] = FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    if BREVO_API_KEY:
        name, address = parseaddr(FROM)
        if not address or "@" not in address or address.endswith("@localhost"):
            raise RuntimeError("verified mail sender not configured")
        payload = json.dumps({
            "sender": {"name": name or "InterviewAnchor", "email": address},
            "to": [{"email": to}], "subject": subject, "textContent": text,
        }).encode("utf-8")
        # Fixed HTTPS origin, no redirects and no retries: keys cannot follow a
        # redirect, and a timed-out submission cannot silently duplicate a code.
        connection = http.client.HTTPSConnection("api.brevo.com", timeout=15,
                                                 context=ssl.create_default_context())
        try:
            connection.request("POST", "/v3/smtp/email", body=payload, headers={
                "api-key": BREVO_API_KEY, "Content-Type": "application/json",
                "Accept": "application/json",
            })
            response = connection.getresponse()
            if response.status != 201:
                # Never put the response, code, email address or key in logs.
                raise RuntimeError("transactional mail provider rejected delivery")
            result = json.loads(response.read(65536))
            if not result.get("messageId"):
                raise RuntimeError("transactional mail provider did not confirm delivery")
        finally:
            connection.close()
        return
    ctx = ssl.create_default_context()
    with smtplib.SMTP(HOST, PORT, timeout=15) as s:
        s.starttls(context=ctx)
        if USER:
            s.login(USER, PASSWORD)
        s.send_message(msg)
