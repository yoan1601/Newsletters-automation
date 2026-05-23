# Workflow: Render and Review

## Objective
Render the newsletter HTML from structured content, verify it meets visual identity and deliverability standards, and prepare it for send.

## Required Inputs
- `.tmp/newsletter_content.json` — structured content (produced by `generate_newsletter.md` Step 2)
- Infographic PNGs in `.tmp/` (if any)

## Steps

### Step 1 — Render HTML
```
python tools/render_newsletter.py --content .tmp/newsletter_content.json
```

Output: `.tmp/newsletter_YYYY-MM-DD.html`

The renderer:
- Loads `tools/templates/newsletter.html.j2`
- Encodes infographics as base64 inline images
- Encodes logo from `brand_assets/logo.png` as base64 inline
- Runs premailer to inline all CSS (email-safe output)
- Warns if output exceeds 90 KB

### Step 2 — File Size Check
Check the terminal output for the file size warning.

| Size | Action |
|---|---|
| < 70 KB | No action needed |
| 70–90 KB | Monitor — acceptable but near limit |
| > 90 KB | Drop 1 infographic and re-render. See fix below. |

**Fix for oversized newsletter:**
1. Identify which infographic PNG is largest (`dir .tmp\*.png` or `ls -lh .tmp/*.png`)
2. Either remove that infographic from `newsletter_content.json`, or re-generate it with a simpler prompt
3. Re-run `render_newsletter.py`

### Step 3 — Visual Review Checklist
Open `.tmp/newsletter_YYYY-MM-DD.html` in a browser and verify each item:

**Structure**
- [ ] Header: Deep Navy background, Signal Green eyebrow label, issue title, date
- [ ] Logo renders in header (if `brand_assets/logo.png` exists)
- [ ] 3–5 sections, each with a numbered label and bold headline
- [ ] Light Gray dividers between all sections
- [ ] Footer: sources list + metadata line

**Typography hierarchy**
- [ ] H1 title (large, Semibold, Off-White on Navy)
- [ ] Section titles (18–20px, Semibold, Navy)
- [ ] Body text (15px, Regular, Slate)
- [ ] Source links (small, muted gray)

**Brand rules**
- [ ] Signal Green used in max 2 places (eyebrow label + at most 1 callout block)
- [ ] No more than 2 callout blocks total
- [ ] Each section covers exactly 1 idea — no section is a general "overview"
- [ ] High whitespace — no section feels dense or cramped

**Infographics**
- [ ] Images render inline (not broken `<img>` icons)
- [ ] Each image has a descriptive `alt` attribute
- [ ] Captions are present and accurate

**Links**
- [ ] All source URLs in the footer are clickable
- [ ] No `[object Object]` or template artifact text visible

### Step 4 — Content Quality Check
Read through the rendered newsletter as a reader would:

- [ ] `answer_summary` gives a useful 2–3 sentence overview of the topic
- [ ] Each section headline is assertive and specific ("Enterprises Are Cutting Agent Deployment Time by 40%", not "Industry Trends")
- [ ] No section repeats the same point as another
- [ ] Callout blocks (if present) contain genuinely surprising or actionable insights — not generic statements
- [ ] Sources are cited; no claim appears unsupported

### Step 5 — Plain-Text Fallback
The `send_email_gmail.py` tool auto-generates plain text from the HTML. Verify it would be readable by:
- Mentally strip all formatting from a section
- Confirm the key facts are still communicated

If the body text relies heavily on visual layout to convey meaning, add explicit transitions in the text (e.g., "As shown in the chart above:").

### Step 6 — Subject Line Check
The subject line passed to `send_email_gmail.py` must:
- Follow format: `<Newsletter Name> | <Month D, YYYY>` (e.g., "Intelligence Brief | May 23, 2026")
- Be under 60 characters for full display on mobile
- Not contain ALL CAPS, excessive punctuation, or spam-trigger words (FREE, URGENT, !!!)

### Step 7 — Sign Off
If all checks pass, return to `generate_newsletter.md` Step 5 (User Approval Gate).

If any checks fail, fix the issue in `newsletter_content.json` and re-run `render_newsletter.py`.
