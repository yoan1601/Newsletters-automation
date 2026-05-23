# Workflow: Google Setup (One-Time)

## Objective
Authenticate with Google so Gmail and Drive tools work. This is a one-time setup. After completion, tools auto-refresh credentials silently.

## Prerequisites
- A Google account (personal Gmail is fine)
- A Google Cloud project with OAuth 2.0 credentials configured

## Step 1 — Create Google Cloud Project & OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Newsletter Automation")
3. Enable these APIs:
   - Gmail API
   - Google Drive API
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Name: "Newsletter Automation"
7. Click **Create**
8. Download the JSON file → save as `credentials.json` in the project root

**Also configure the OAuth consent screen:**
- User type: External
- App name: Newsletter Automation
- Scopes to add: `gmail.send`, `drive.file`
- Test users: add your own email

## Step 2 — Fill in .env
Open `.env` and fill in:
```
GOOGLE_CLIENT_ID=<from credentials.json>
GOOGLE_CLIENT_SECRET=<from credentials.json>
NEWSLETTER_SENDER_EMAIL=<your Gmail address>
NEWSLETTER_DEFAULT_RECIPIENT=<your Gmail address or list>
NEWSLETTER_DRIVE_FOLDER_ID=<optional — Drive folder ID for newsletter archives>
```

`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are also present in `credentials.json`. Both are needed.

## Step 3 — Run the Auth Tool
```
python tools/google_auth.py
```

This opens a browser window asking you to log in and grant permissions. Click **Allow**.

After granting permission, `token.json` is written to the project root. This file contains your access token and refresh token.

**Important:** `token.json` is gitignored. Never commit it. It gives anyone who has it full Gmail send + Drive access on your account.

## Step 4 — Verify
Test Gmail:
```
python tools/send_email_gmail.py --to <your email> --subject "Test | Setup" --html-file .env
```
(Sending `.env` as a body is harmless — it's just a quick connectivity test. You'll receive an email with raw env content in the body.)

Test Drive:
```
python tools/upload_to_drive.py --file requirements.txt --folder-name "Newsletter Test"
```

You should see a Google Drive link in the output.

## Re-Authentication
Tokens automatically refresh as long as the `refresh_token` in `token.json` is valid.

**Refresh tokens are revoked when:**
- You revoke access at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
- The Google Cloud project is deleted
- The OAuth consent screen is in "Testing" mode and the token is older than 7 days (publish the app to extend this)

**If revoked:** simply run `python tools/google_auth.py` again.

## Notes
- `drive.file` scope only grants access to files created by this application — it cannot read or modify other files in your Drive. This is intentional for least-privilege access.
- `gmail.send` scope only allows sending email — it cannot read, delete, or modify messages in your inbox.
- If you want to send from a different Gmail address later, update `NEWSLETTER_SENDER_EMAIL` in `.env` and re-authenticate with that account's credentials.
