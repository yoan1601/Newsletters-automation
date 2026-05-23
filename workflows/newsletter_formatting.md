# Newsletter Formatting Standard

> **This is the single source of truth for visual identity and content rules.**
> Every newsletter must conform to this standard before it is sent.
> When in doubt, check here — not memory, not past issues.

---

## Brand Tokens

Defined in `config/brand.json`. Never hardcode these values elsewhere.

| Token | Hex | Role |
|---|---|---|
| Navy | `#0B1F3B` | Header background, section titles, callout block background |
| Slate | `#1F2937` | Body text |
| Off-White | `#F8FAFC` | Page background, header H1, callout body text |
| Light Gray | `#E5E7EB` | Dividers, section separators |
| Signal Green | `#10B981` | Accent only — eyebrow label, callout `<strong>` text |

**Font:** Inter (email fallback: Arial, Helvetica, sans-serif)
**Two weights only:** Regular (400) for body, Semibold (600) for headlines and labels.

---

## Layout Constraints

| Rule | Value |
|---|---|
| Container width | 600px max, centered |
| Body padding | 48px left/right |
| Section padding | 40px top/bottom, 48px sides |
| Max email size | 90 KB (Gmail clips above 102 KB) |
| Infographic width | 504px max (inline base64 PNG or JPEG) |

---

## Template Structure

The Jinja2 template at `tools/templates/newsletter.html.j2` renders in this order:

```
[HEADER]  Navy background
  → Logo (if brand_assets/logo.png exists)
  → Eyebrow label (Signal Green, uppercase, 11px)
  → Issue title (Off-White, 26px Semibold)
  → Date (muted gray, 12px)

[SUMMARY BLOCK]  Off-White background, Signal Green left border
  → answer_summary field (2–3 sentences)

[SECTIONS]  Repeated for each section in order
  → Light Gray divider (full width, 1px)
  → Section number (Signal Green, 11px, uppercase, zero-padded e.g. "01")
  → Section title (Navy, 19px Semibold)
  → Body paragraphs (Slate, 15px, 1.75 line-height)
  → Callout block (Navy background, Signal Green <strong>) — optional
  → Infographic (base64 inline, 504px) — optional
  → Source link (muted gray, 12px) — optional

[FOOTER]
  → Sources list (linked, muted gray)
  → Metadata line: date · section count · sender email
```

---

## Content Rules

### Sections
- **3–5 sections per issue.** Never fewer, never more.
- **1 idea per section.** If a section covers two ideas, split it.
- Section titles must be assertive and specific:
  - Good: "Enterprises Cut Agent Deployment Time by 40%"
  - Bad: "Industry Trends", "Overview", "What's New"
- Body: 2–3 paragraphs per section. No walls of text.

### Signal Green accent — max 2 uses per issue
The eyebrow label counts as 1. That leaves at most 1 callout block with Signal Green `<strong>` text.

### Callout blocks — max 2 per issue
Use only for genuinely surprising or actionable insights. Never use callouts for generic summaries or restatements of the section body.

### Answer summary
The `answer_summary` field at the top of the newsletter must:
- Be 2–3 sentences
- Give a useful overview of the topic — not a teaser or headline
- Come from the Tavily `answer` field in `research_results.json`

### Subject line
Format: `<Newsletter Name> | <Month D, YYYY>`
Example: `Intelligence Brief | May 23, 2026`
- Under 60 characters for full mobile display
- No ALL CAPS, no `!`, no spam-trigger words (FREE, URGENT, EXCLUSIVE)

---

## `newsletter_content.json` Schema

The renderer reads this file. Every field name and type must match exactly.

```json
{
  "title": "string — issue title, used as <title> and header H1",
  "eyebrow": "string — defaults to 'Intelligence Brief'",
  "answer_summary": "string — 2–3 sentence overview",
  "sections": [
    {
      "title": "string — section headline",
      "body": "string — paragraphs separated by \\n\\n",
      "callout": "string | omit — key insight (max 2 per newsletter)",
      "infographic_path": "string | omit — relative path to .tmp/*.jpg or .tmp/*.png",
      "infographic_alt": "string | omit — describes what the image shows",
      "infographic_caption": "string | omit — caption below the image",
      "source_url": "string | omit — article URL",
      "source_label": "string | omit — article title (falls back to URL)"
    }
  ],
  "sources": [
    {"title": "string", "url": "string"}
  ]
}
```

---

## Infographic Rules

- Generate for: data comparisons, process/system diagrams, multi-component frameworks.
- Skip for: single statistics, simple timelines, anything prose can cover clearly.
- Style prompt suffix: `"Style: systems diagram, Deep Navy / Off-White palette, Signal Green accent, minimal, executive."`
- Target size: under 40 KB per image (use `google/nano-banana` via kie.ai `createTask` endpoint — outputs JPEG at 480px wide, ~11 KB).
- If total HTML > 90 KB: drop the largest infographic and re-render.

---

## Pre-Send Checklist

Run through this before every send. Referenced in `workflows/render_and_review.md`.

**Structure**
- [ ] Header: Navy background, Signal Green eyebrow, title, date
- [ ] 3–5 sections with numbered labels and specific headlines
- [ ] Dividers between all sections
- [ ] Footer: sources + metadata line

**Brand compliance**
- [ ] Signal Green appears in max 2 places
- [ ] Max 2 callout blocks
- [ ] No section covers more than 1 idea
- [ ] High whitespace — no section feels dense

**Technical**
- [ ] All images render inline (no broken `<img>` icons)
- [ ] File size under 90 KB
- [ ] All source URLs clickable
- [ ] No template artifacts (`[object Object]`, `{{ }}` remnants)

**Content**
- [ ] `answer_summary` is informative, not a teaser
- [ ] Every section headline is specific and assertive
- [ ] No two sections repeat the same point
- [ ] Callout blocks contain genuinely surprising or actionable insights
