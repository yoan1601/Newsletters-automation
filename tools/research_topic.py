"""
Research a topic using Tavily and save structured results to .tmp/research_results.json.

Usage:
    python tools/research_topic.py --topic "AI agents in enterprise" [--days 30] [--max-results 10]

Output: .tmp/research_results.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TMP_DIR = Path(".tmp")
TMP_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = TMP_DIR / "research_results.json"


def research(topic: str, days: int, max_results: int) -> list[dict]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY not set in .env")
        sys.exit(1)

    client = TavilyClient(api_key=api_key)

    print(f"Searching Tavily for: '{topic}' (last {days} days, max {max_results} results)...")

    response = client.search(
        query=topic,
        search_depth="advanced",
        max_results=max_results,
        days=days,
        include_answer=True,
        include_raw_content=False,
    )

    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "excerpt": r.get("content", ""),
            "published_date": r.get("published_date", ""),
            "score": r.get("score", 0),
        })

    # Sort by relevance score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    output = {
        "topic": topic,
        "search_date": datetime.now().isoformat(),
        "days_searched": days,
        "answer_summary": response.get("answer", ""),
        "results": results,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Found {len(results)} results. Saved to {OUTPUT_PATH}")

    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['title']} — {r['url']}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research a topic with Tavily")
    parser.add_argument("--topic", required=True, help="Topic to research")
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.getenv("TAVILY_SEARCH_DAYS", 30)),
        help="Recency window in days (default: 30)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=int(os.getenv("TAVILY_MAX_RESULTS", 10)),
        help="Maximum number of results (default: 10)",
    )
    args = parser.parse_args()
    research(args.topic, args.days, args.max_results)
