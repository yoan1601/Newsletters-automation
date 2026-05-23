"""
Send a newsletter email via Gmail API using OAuth credentials.
Sends as multipart/alternative (HTML + plain-text fallback) for deliverability.

Usage:
    python tools/send_email_gmail.py --to recipient@example.com --subject "AI Weekly | 2026-05-23" --html-file .tmp/newsletter_2026-05-23.html
    python tools/send_email_gmail.py --to recipient@example.com --subject "..." --html-file ... --plain-text-file .tmp/plaintext.txt

The plain-text body is auto-generated from the HTML if --plain-text-file is omitted.
"""

import argparse
import base64
import os
import re
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import config as cfg
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "./token.json"))


def _get_credentials() -> Credentials:
    if not TOKEN_PATH.exists():
        print(
            f"ERROR: token.json not found at {TOKEN_PATH}\n"
            "Run tools/google_auth.py first to authenticate."
        )
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print("Token expired — refreshing silently...")
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        else:
            print("ERROR: Token is invalid and cannot be refreshed. Run tools/google_auth.py again.")
            sys.exit(1)

    return creds


def _html_to_plain_text(html: str) -> str:
    # Strip HTML tags and normalize whitespace for the plain-text fallback
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def send(
    to: str,
    subject: str,
    html_body: str,
    plain_text_body: str | None = None,
    sender: str | None = None,
) -> str:
    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    if not plain_text_body:
        plain_text_body = _html_to_plain_text(html_body)

    sender_email = sender or cfg.newsletter().get("sender_email") or "me"

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to

    # Plain-text part first (fallback for clients that can't render HTML)
    message.attach(MIMEText(plain_text_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()

    message_id = result.get("id", "unknown")
    print(f"Email sent successfully. Gmail message ID: {message_id}")
    return message_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a newsletter email via Gmail")
    parser.add_argument("--to", default=cfg.newsletter().get("default_recipient"), help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--html-file", required=True, help="Path to rendered HTML newsletter file")
    parser.add_argument("--plain-text-file", default=None, help="Path to plain-text version (auto-generated if omitted)")
    parser.add_argument("--from", dest="sender", default=None, help="Sender email (default: NEWSLETTER_SENDER_EMAIL)")
    args = parser.parse_args()

    if not args.to:
        print("ERROR: --to is required (or set default_recipient in config/newsletter.json)")
        sys.exit(1)

    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"ERROR: HTML file not found: {html_path}")
        sys.exit(1)

    html_body = html_path.read_text(encoding="utf-8")

    plain_text_body = None
    if args.plain_text_file:
        pt_path = Path(args.plain_text_file)
        if pt_path.exists():
            plain_text_body = pt_path.read_text(encoding="utf-8")

    send(args.to, args.subject, html_body, plain_text_body, args.sender)
