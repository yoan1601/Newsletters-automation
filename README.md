# Newsletter Automation — WAT Framework

An agentic newsletter pipeline built on the **WAT architecture** (Workflows · Agents · Tools). Given a topic, it researches the web, drafts structured content, generates infographics, renders a branded HTML email, and sends it via Gmail — archiving each issue to Google Drive.

---

## How It Works

The pipeline separates probabilistic AI reasoning (the agent) from deterministic execution (Python scripts). Each layer has a single responsibility:

| Layer | What it is | Where it lives |
|---|---|---|
| **Workflows** | Markdown SOPs — step-by-step instructions the agent follows | `workflows/` |
| **Agent** | Claude Code — reads workflows, decides what to run, recovers from errors | (you're here) |
| **Tools** | Python scripts that do the actual work (API calls, rendering, file I/O) | `tools/` |

### Full pipeline (triggered by `workflows/generate_newsletter.md`)

```
Topic input
  → Research (Tavily search + deduplication)
  → Content draft (structured JSON with sections)
  → Infographic generation (kie.ai image API)
  → HTML render (Jinja2 template + inline CSS)
  → User approval gate
  → Send via Gmail API
  → Archive to Google Drive
```

---

## Directory Layout

```
.tmp/               # Temporary files (scraped data, rendered HTML, JSON). Disposable.
brand_assets/       # Visual Identity System — color palette, typography, layout rules
config/
  brand.json        # Brand tokens (colors, fonts)
  newsletter.json   # Runtime config (sender email, recipient, Drive folder ID)
tools/              # Python scripts — one purpose each
  config.py         # Loads .env and config/
  extract_article.py         # Full-text extraction via trafilatura
  generate_infographic.py    # kie.ai image generation
  google_auth.py             # One-time OAuth setup for Gmail + Drive
  render_newsletter.py       # Jinja2 → HTML with inlined CSS
  research_topic.py          # Tavily web search
  send_email_gmail.py        # Gmail API send
  upload_to_drive.py         # Google Drive upload
  templates/
    newsletter.html.j2       # Branded email template
workflows/          # SOPs the agent reads at runtime
  generate_newsletter.md     # Master workflow — orchestrates all steps
  research_and_summarize.md  # Research sub-workflow
  render_and_review.md       # Render + visual QA workflow
  newsletter_formatting.md   # Content and formatting rules
  google_setup.md            # One-time Google OAuth setup guide
.env                # API keys (never committed — see .gitignore)
credentials.json    # Google OAuth client credentials (never committed)
token.json          # Google OAuth token (never committed)
requirements.txt    # Python dependencies
```

---

## Prerequisites

- Python 3.10+
- A [Tavily](https://tavily.com) API key (web research)
- A [kie.ai](https://kie.ai) API key (infographic generation)
- A Google Cloud project with Gmail API + Drive API enabled, and an OAuth 2.0 Desktop client

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure `.env`

Create `.env` in the project root:

```env
TAVILY_API_KEY=tvly-...
KIE_API_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
NEWSLETTER_SENDER_EMAIL=you@gmail.com
NEWSLETTER_DEFAULT_RECIPIENT=you@gmail.com
NEWSLETTER_DRIVE_FOLDER_ID=<optional Drive folder ID>
```

### 3. Authenticate with Google (one-time)

Follow `workflows/google_setup.md` for full instructions, or run:

```bash
python tools/google_auth.py
```

A browser window opens — log in and grant Gmail send + Drive file permissions. `token.json` is written automatically and refreshes silently on subsequent runs.

---

## Usage

Open Claude Code in this directory and give it a topic:

```
Generate a newsletter on "AI agents in enterprise 2026"
```

Claude reads `workflows/generate_newsletter.md`, runs each tool in sequence, presents a preview for your approval, then sends the email and archives the HTML to Drive.

You can also run individual tools directly:

```bash
# Research only
python tools/research_topic.py --topic "data center energy 2026" --days 14

# Render only (from existing content JSON)
python tools/render_newsletter.py --content .tmp/newsletter_content.json

# Send only (from existing HTML)
python tools/send_email_gmail.py --to you@gmail.com --subject "Brief | May 23, 2026" --html-file .tmp/newsletter_2026-05-23.html
```

---

## Brand System

The newsletter uses a minimal, executive visual identity defined in `brand_assets/Visual Identity System.md`:

- **Deep Navy** `#0B1F3B` — primary background
- **Off-White** `#F8FAFC` — body background
- **Signal Green** `#10B981` — accent (max 2 uses per issue)
- **Typography** — Inter / SF Pro, two weights, strict hierarchy
- **Layout** — high whitespace, 1 idea per section, divider lines between sections

Content rules: 3–5 sections, 2–3 paragraphs per section, max 2 callout blocks.

---

## Security Notes

- `.env`, `credentials.json`, and `token.json` are gitignored and must never be committed
- `credentials.json` grants OAuth access to your Google account — treat it like a password
- `token.json` gives Gmail send + Drive write access — rotate by running `tools/google_auth.py` again if compromised
- `drive.file` scope limits Drive access to files created by this app only (least-privilege)
- `gmail.send` scope allows sending only — it cannot read your inbox
