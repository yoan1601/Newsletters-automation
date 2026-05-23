# Workflow: Research and Summarize

## Objective
Research a topic using Tavily, filter for relevance and freshness, deduplicate against previously used URLs, and optionally extract full article body for the top sources.

## Required Inputs
- `topic` — research query string
- `days` — recency window (default: 30; use 7 for fast-moving topics like AI news)
- `max_results` — number of Tavily results to fetch (default: 10)

## Steps

### Step 1 — Run Tavily Search
```
python tools/research_topic.py --topic "<topic>" --days <days> --max-results <max_results>
```

Output: `.tmp/research_results.json`

Fields in each result:
- `title`, `url`, `excerpt`, `published_date`, `score` (0–1 relevance)

### Step 2 — Deduplication Check
Load `.tmp/seen_urls.json` if it exists. Filter out any results whose `url` is already in the seen list.

If `.tmp/seen_urls.json` does not exist, create it as an empty array `[]`.

**After filtering:** if fewer than 4 unique results remain, widen the search:
- Increase `--days` (e.g., 30 → 60)
- Try a rephrased topic (e.g., add "2026", add "latest", or break into a sub-topic)

### Step 3 — Relevance Triage
From the deduplicated results, select 5–8 best sources based on:
1. Relevance score (prefer > 0.5)
2. Recency (prefer results from the last 14 days over older ones)
3. Source quality (industry publications, research firms, credible news > personal blogs)
4. Diversity (cover different angles of the topic — don't use 5 sources saying the same thing)

Discard results with score < 0.3 or excerpt shorter than 50 words (likely paywalled or low-quality).

### Step 4 — Deep Extraction (Top 2–3 Sources)
For the top 2–3 most relevant sources, extract full article body:

```
python tools/extract_article.py --url "<url>"
```

Use extracted text to enrich newsletter section bodies beyond what the Tavily excerpt provides.

**Skip if:** the URL returns an empty extraction (trafilatura failure) — use Tavily excerpt instead. Never fail the workflow because a single URL couldn't be extracted.

### Step 5 — Update Seen URLs Log
Append all selected URLs to `.tmp/seen_urls.json`:

```json
["https://...", "https://...", "https://..."]
```

This prevents the same sources from appearing in future issues.

**Note:** `.tmp/seen_urls.json` is disposable per the framework rules. For persistent deduplication across sessions, copy it to Google Drive or a Google Sheet after each run.

### Step 6 — Return Summary to Agent
Produce a structured summary in memory for the agent to use in Step 2 of `generate_newsletter.md`:

```
- answer_summary: <Tavily's answer field, lightly edited>
- selected_sources: list of {title, url, excerpt or extracted_text}
- suggested_sections: 3-5 thematic groupings of the sources
```

Suggested sections should be distinct angles, not summaries of individual articles. Examples:
- "The Business Case" vs "The Technical Risks" vs "Who's Actually Deploying This"
- "What Changed This Quarter" vs "What to Watch Next"

## Notes
- Tavily's `answer` field is a pre-synthesized paragraph — use it as the newsletter's `answer_summary` with minor edits for tone
- If a topic is too broad, Tavily returns generic results. Narrow it: "AI agents in legal ops 2026" outperforms "AI agents"
- If a topic is too narrow, fewer than 4 results come back. Broaden it or increase `--days`
