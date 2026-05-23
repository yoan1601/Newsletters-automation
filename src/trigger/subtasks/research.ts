import { task } from "@trigger.dev/sdk/v3";
import { runPython, readTmpJson } from "../utils/run-python";

export interface ResearchResult {
  title: string;
  url: string;
  excerpt: string;
  published_date: string;
  score: number;
}

export interface ResearchOutput {
  topic: string;
  search_date: string;
  days_searched: number;
  answer_summary: string;
  results: ResearchResult[];
}

export interface ResearchInput {
  topic: string;
  days?: number;
  maxResults?: number;
}

export const researchTask = task({
  id: "newsletter-research",
  maxDuration: 60,
  retry: { maxAttempts: 3, minTimeoutInMs: 5000 },
  run: async (input: ResearchInput): Promise<ResearchOutput> => {
    const { topic, days = 30, maxResults = 10 } = input;

    runPython("tools/research_topic.py", [
      "--topic", topic,
      "--days", String(days),
      "--max-results", String(maxResults),
    ]);

    return readTmpJson<ResearchOutput>("research_results.json");
  },
});
