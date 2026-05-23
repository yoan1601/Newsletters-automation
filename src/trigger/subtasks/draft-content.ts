import { task, logger } from "@trigger.dev/sdk/v3";
import Anthropic from "@anthropic-ai/sdk";
import { writeTmpJson } from "../utils/run-python";
import type { ResearchOutput } from "./research";

export interface NewsletterSection {
  title: string;
  body: string;
  callout?: string;
  infographic_path?: string;
  infographic_alt?: string;
  infographic_caption?: string;
  source_url?: string;
  source_label?: string;
}

export interface NewsletterContent {
  title: string;
  eyebrow: string;
  answer_summary: string;
  sections: NewsletterSection[];
  sources: Array<{ title: string; url: string }>;
}

export interface DraftContentInput {
  research: ResearchOutput;
  issueTitleOverride?: string;
}

const SYSTEM_PROMPT = `You are a professional newsletter editor writing an executive intelligence brief.
Your output must be valid JSON matching the exact schema provided. No prose, no markdown, no explanation — only the JSON object.

BRAND RULES (non-negotiable):
- 3 to 5 sections maximum. Each section covers exactly 1 idea.
- Section titles: assertive and specific. Never "Overview", "Introduction", or "What's New".
- Body: 2–3 paragraphs per section separated by \\n\\n. No bullet points. No walls of text.
- Callout blocks: max 2 per newsletter. Use only for genuinely surprising or actionable insights.
- answer_summary: 2–3 sentences from the Tavily answer, lightly edited for executive tone.
- Sources: every section must reference 1 source from the provided list.
- infographic_alt: always include for the first 2 sections — describe what the infographic should show.`;

export const draftContentTask = task({
  id: "newsletter-draft-content",
  maxDuration: 120,
  retry: { maxAttempts: 2, minTimeoutInMs: 5000 },
  run: async (input: DraftContentInput): Promise<NewsletterContent> => {
    const { research, issueTitleOverride } = input;

    const client = new Anthropic();

    const now = new Date();
    const monthDay = now.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
    const issueTitle = issueTitleOverride ?? `${research.topic} | ${monthDay}`;

    const topResults = research.results.slice(0, 8);
    const sourcesContext = topResults
      .map(
        (r, i) =>
          `[${i + 1}] "${r.title}" (${r.published_date})\nURL: ${r.url}\nExcerpt: ${r.excerpt}`
      )
      .join("\n\n");

    const userPrompt = `Topic: ${research.topic}
Issue title: ${issueTitle}

Tavily synthesized answer (use as answer_summary base):
${research.answer_summary}

Source articles:
${sourcesContext}

Produce a newsletter content JSON object. Output ONLY valid JSON, no other text.

Required schema:
{
  "title": "${issueTitle}",
  "eyebrow": "Intelligence Brief",
  "answer_summary": "<2-3 sentence overview>",
  "sections": [
    {
      "title": "<assertive headline>",
      "body": "<paragraph 1>\\n\\n<paragraph 2>",
      "callout": "<optional — only if genuinely surprising>",
      "infographic_alt": "<describe what infographic should show — include for first 2 sections>",
      "infographic_caption": "<optional>",
      "source_url": "<URL from sources list>",
      "source_label": "<title from sources list>"
    }
  ],
  "sources": [
    {"title": "<title>", "url": "<url>"}
  ]
}`;

    logger.log("Calling Claude API for content drafting", {
      topic: research.topic,
      sourceCount: topResults.length,
    });

    const message = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      messages: [{ role: "user", content: userPrompt }],
    });

    const rawContent = message.content[0];
    if (rawContent.type !== "text") {
      throw new Error("Claude returned non-text content");
    }

    // Strip any accidental markdown code fences
    const jsonText = rawContent.text
      .replace(/^```json\s*/i, "")
      .replace(/^```\s*/i, "")
      .replace(/```$/i, "")
      .trim();

    let content: NewsletterContent;
    try {
      content = JSON.parse(jsonText);
    } catch (e) {
      logger.error("Failed to parse Claude response as JSON", {
        raw: jsonText.slice(0, 500),
      });
      throw new Error(`Claude did not return valid JSON: ${String(e)}`);
    }

    writeTmpJson("newsletter_content.json", content);
    logger.log("Content drafted", { sectionCount: content.sections.length, title: content.title });

    return content;
  },
});
