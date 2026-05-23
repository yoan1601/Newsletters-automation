# Workflow: Generate Newsletter

## Objective
Produce a fully styled HTML newsletter on a given topic and send it via Gmail, archiving to Google Drive.

## Required Inputs
- `topic` — the subject of this newsletter issue (e.g., "AI agents in enterprise 2026")
- `recipient` — email address to send to (or use `NEWSLETTER_DEFAULT_RECIPIENT` from `.env`)
- `issue_title` — optional human-readable title (e.g., "AI Agents Weekly | May 2026"); auto-generated from topic + date if omitted

## Steps

### Step 1 — Research
Run the research sub-workflow: `workflows/research_and_summarize.md`

Expected output: `.tmp/research_results.json`

### Step 2 — Draft Content Structure
Using the research results, draft a `newsletter_content.json` file at `.tmp/newsletter_content.json`.

**Structure:**
```json
{
  "title": "<issue_title>",
  "eyebrow": "Intelligence Brief",
  "answer_summary": "<2-3 sentence overview from Tavily answer field>",
  "sections": [
    {
      "title": "<concise section headline — 1 idea>",
      "body": "<paragraph 1>\n\n<paragraph 2>",
      "callout": "<optional key insight — used max 2× per newsletter>",
      "infographic_path": "<filled in at Step 3, or omit>",
      "infographic_alt": "<describe what the infographic shows>",
      "infographic_caption": "<optional caption>",
      "source_url": "<article URL>",
      "source_label": "<article title>"
    }
  ],
  "sources": [
    {"title": "<article title>", "url": "<url>"}
  ]
}
```

**Content rules (Visual Identity System):**
- 3–5 sections maximum; 1 idea per section
- Short, assertive headlines — no vague titles like "Overview"
- Body: 2–3 paragraphs per section; no dense walls of text
- Callout blocks: max 2 total; use only for genuinely surprising or actionable insights
- Signal Green accent elements: max 2 per newsletter
- Divider lines separate sections automatically
- Strong hierarchy: section number → title → body → callout → source

### Step 3 — Generate Infographics
For 2–3 sections where a visual would add clarity, call `tools/generate_infographic.py`.

**When to generate an infographic:**
- Data comparisons (e.g., adoption rates, market share, before/after)
- Systems or process diagrams
- Frameworks with multiple components

**Prompt guidelines:**
- Describe what the infographic should show, not how to draw it
- Append: "Style: systems diagram, Deep Navy / Off-White palette, Signal Green accent, minimal, executive."
- Keep prompts under 300 words

**Run:**
```
python tools/generate_infographic.py --prompt "<description>" --name "<short_name>"
```

Update `infographic_path` in `newsletter_content.json` for each generated image.

**Size check:** Each PNG in `.tmp/` should be under 40KB after resize. If a PNG is large, the total email may hit Gmail's 102KB clip threshold — reduce the number of infographics or omit the largest one.

### Step 4 — Render HTML
```
python tools/render_newsletter.py --content .tmp/newsletter_content.json
```

Output: `.tmp/newsletter_YYYY-MM-DD.html`

Open the HTML file in a browser to verify:
- Visual hierarchy is correct (Navy header → numbered sections → footer)
- Infographics render inline (not broken)
- No section exceeds 3 dense paragraphs
- Max 2 Signal Green callout elements visible
- File size is under 90 KB (check terminal output warning)

**If the file is over 90 KB:** reduce infographic count or prompt for simpler images.

### Step 5 — User Approval Gate
Before sending, present a summary to the user:
- Issue title
- Number of sections
- Topics covered
- Recipients
- Drive folder destination
- Rendered HTML file path for browser preview

**Ask:** "Ready to send? (yes / revise)"

If revise: return to Step 2 or Step 3 as needed.

### Step 6 — Send Email
```
python tools/send_email_gmail.py \
  --to <recipient> \
  --subject "<issue_title>" \
  --html-file .tmp/newsletter_YYYY-MM-DD.html
```

Plain-text fallback is auto-generated from the HTML.

**Subject line format:** `<Newsletter Name> | <Month D, YYYY>` (e.g., "Intelligence Brief | May 23, 2026")
This prevents Gmail from threading separate issues together.

### Step 7 — Archive to Drive
```
python tools/upload_to_drive.py --file .tmp/newsletter_YYYY-MM-DD.html
```

Save the returned Drive link. Report it to the user as the permanent archive URL.

## Error Handling

| Error | Recovery |
|---|---|
| Tavily returns 0 results | Broaden topic or increase `--days`; try alternate phrasings |
| kie.ai task times out | Skip that infographic; note it in the issue footer or retry once |
| kie.ai returns 404 on any endpoint | Correct endpoints: POST `/api/v1/jobs/createTask`, GET `/api/v1/jobs/recordInfo?taskId=<id>`. Model: `google/nano-banana`. Output: JPEG at 480px wide (~11KB). |
| kie.ai task stuck at GENERATING 0.00 forever | Wrong model — `gpt4o-image` endpoint is unreliable; use `createTask` with `google/nano-banana` instead |
| kie.ai PNG > 40KB | Re-prompt with "simpler diagram, fewer elements" |
| Gmail send fails (token expired) | Run `tools/google_auth.py` to refresh, then retry |
| Drive upload fails | Save HTML locally and provide file path to user as fallback |
| render_newsletter warns > 90KB | Drop 1 infographic and re-render |

## Output
- Sent email in recipient's inbox
- HTML archived in Google Drive with shareable link
- All intermediates in `.tmp/` (disposable)

## Notes
- Run `pip install -r requirements.txt` before first use
- Run `tools/google_auth.py` before first use (one-time) — requires `credentials.json` in project root (download from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs)
- The seen-URLs log lives at `.tmp/seen_urls.json` — managed by `workflows/research_and_summarize.md`
- On Windows: `tools/research_topic.py` and `tools/render_newsletter.py` both require explicit `encoding="utf-8"` in file writes — already patched in both tools
