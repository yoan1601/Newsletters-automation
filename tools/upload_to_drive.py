"""
Upload a local file to Google Drive and return its shareable URL.
Creates the target folder if it doesn't exist.

Usage:
    python tools/upload_to_drive.py --file .tmp/newsletter_2026-05-23.html
    python tools/upload_to_drive.py --file .tmp/newsletter_2026-05-23.html --folder-id "1abc...xyz"
    python tools/upload_to_drive.py --file .tmp/newsletter_2026-05-23.html --folder-name "Newsletters"
"""

import argparse
import os
import sys
from pathlib import Path

import config as cfg
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "./token.json"))

MIME_TYPES = {
    ".html": "text/html",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".json": "application/json",
    ".txt": "text/plain",
}


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
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        else:
            print("ERROR: Token invalid. Run tools/google_auth.py again.")
            sys.exit(1)

    return creds


def _get_or_create_folder(service, folder_name: str) -> str:
    query = (
        f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' "
        "and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        folder_id = folders[0]["id"]
        print(f"Using existing Drive folder '{folder_name}' (id: {folder_id})")
        return folder_id

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    folder_id = folder["id"]
    print(f"Created Drive folder '{folder_name}' (id: {folder_id})")
    return folder_id


def upload(file_path: Path, folder_id: str | None = None, folder_name: str | None = None) -> str:
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)

    # Resolve folder
    if not folder_id:
        folder_id = cfg.newsletter().get("drive_folder_id")
    if not folder_id and folder_name:
        folder_id = _get_or_create_folder(service, folder_name)
    if not folder_id:
        folder_id = _get_or_create_folder(service, "Newsletters")

    mime_type = MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream")

    file_metadata = {
        "name": file_path.name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=False)

    print(f"Uploading {file_path.name} to Drive...")
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
    ).execute()

    file_id = uploaded["id"]
    view_link = uploaded.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

    # Make it accessible to anyone with the link
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    print(f"Uploaded successfully.")
    print(f"View link: {view_link}")
    return view_link


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a file to Google Drive")
    parser.add_argument("--file", required=True, help="Path to the file to upload")
    parser.add_argument("--folder-id", default=None, help="Target Drive folder ID")
    parser.add_argument("--folder-name", default=None, help="Target Drive folder name (created if it doesn't exist)")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    upload(file_path, args.folder_id, args.folder_name)
