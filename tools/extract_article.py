"""
Extract clean article text from a URL using trafilatura.
Used when Tavily excerpts are too shallow and full article body is needed.

Usage:
    python tools/extract_article.py --url "https://example.com/article"

Output: .tmp/article_{url_hash}.txt
        Prints extracted text to stdout on success, empty string on failure.
"""

import argparse
import hashlib
import sys
from pathlib import Path

import trafilatura

TMP_DIR = Path(".tmp")
TMP_DIR.mkdir(exist_ok=True)


def extract(url: str) -> str:
    print(f"Extracting article from: {url}")

    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        print(f"WARNING: Could not fetch URL: {url}", file=sys.stderr)
        return ""

    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )

    if not text:
        print(f"WARNING: Could not extract text from: {url}", file=sys.stderr)
        return ""

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    output_path = TMP_DIR / f"article_{url_hash}.txt"
    output_path.write_text(text, encoding="utf-8")

    word_count = len(text.split())
    print(f"Extracted {word_count} words. Saved to {output_path}")
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract article text from a URL")
    parser.add_argument("--url", required=True, help="URL to extract text from")
    args = parser.parse_args()

    result = extract(args.url)
    if result:
        print("\n--- Extracted Text Preview (first 500 chars) ---")
        print(result[:500])
    else:
        sys.exit(1)
