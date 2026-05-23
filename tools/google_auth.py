"""
One-time Google OAuth setup. Run this manually before using any Google tools.
Grants Gmail (send) + Drive (file create/read) scopes.
Writes token.json for subsequent tool runs.

Usage: python tools/google_auth.py
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive.file",
]

CREDENTIALS_PATH = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json"))
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "./token.json"))


def authenticate():
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        print(f"Already authenticated. Token at: {TOKEN_PATH}")
        return creds

    if creds and creds.expired and creds.refresh_token:
        print("Token expired — refreshing silently...")
        creds.refresh(Request())
    else:
        if not CREDENTIALS_PATH.exists():
            print(
                f"ERROR: credentials.json not found at {CREDENTIALS_PATH}\n"
                "Download it from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs."
            )
            raise FileNotFoundError(f"Missing {CREDENTIALS_PATH}")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            SCOPES,
            # access_type=offline ensures a refresh_token is returned so
            # unattended runs can renew the token without browser intervention.
        )
        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent",  # force consent screen to always get refresh_token
        )

    TOKEN_PATH.write_text(creds.to_json())
    print(f"Authentication successful. Token saved to: {TOKEN_PATH}")
    return creds


if __name__ == "__main__":
    authenticate()
    print("\nSetup complete. You can now use tools/send_email_gmail.py and tools/upload_to_drive.py.")
