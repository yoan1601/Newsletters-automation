"""
Render the newsletter HTML from structured content JSON.
Loads the Jinja2 template, injects content + brand assets + infographic images,
then runs premailer to inline all CSS (required for Gmail/Outlook compatibility).

Input:  --content  path to a JSON file (see schema below)
        --output   optional output path (default: .tmp/newsletter_{date}.html)

Content JSON schema:
{
  "title": "AI Agents in Enterprise — May 2026",
  "eyebrow": "Intelligence Brief",          // optional, defaults to "Intelligence Brief"
  "answer_summary": "One-paragraph overview...",
  "sections": [
    {
      "title": "Section headline",
      "body": "Paragraph text.\\n\\nSecond paragraph.",
      "callout": "Key insight in Signal Green callout box.",  // optional
      "infographic_path": ".tmp/infographic_adoption.png",   // optional
      "infographic_alt": "Chart: AI adoption by industry",   // optional
      "infographic_caption": "Source: Gartner 2026",         // optional
      "source_url": "https://example.com/article",           // optional
      "source_label": "Gartner Report"                       // optional
    }
  ],
  "sources": [                              // footer source list
    {"title": "Article Title", "url": "https://..."}
  ]
}

Usage:
    python tools/render_newsletter.py --content .tmp/newsletter_content.json
    python tools/render_newsletter.py --content .tmp/newsletter_content.json --output .tmp/my_issue.html
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import config as cfg
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from premailer import transform

load_dotenv()

TEMPLATE_DIR = Path(__file__).parent / "templates"
TMP_DIR = Path(".tmp")
TMP_DIR.mkdir(exist_ok=True)


def load_base64_image(path_str: str) -> str | None:
    path = Path(path_str)
    if not path.exists():
        print(f"WARNING: Image not found at {path}, skipping.", file=sys.stderr)
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def render(content: dict, output_path: Path) -> Path:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("newsletter.html.j2")

    # Resolve date
    if sys.platform == "win32":
        date = content.get("date") or datetime.now().strftime("%B %d, %Y").replace(" 0", " ")
    else:
        date = content.get("date") or datetime.now().strftime("%B %-d, %Y")

    # Load logo as base64 if it exists
    logo_path = cfg.brand().get("logo_path", "./brand_assets/logo.png")
    logo_base64 = load_base64_image(logo_path) if Path(logo_path).exists() else None

    # Resolve infographic base64 for each section
    sections = content.get("sections", [])
    for section in sections:
        infographic_path = section.pop("infographic_path", None)
        if infographic_path:
            section["infographic_base64"] = load_base64_image(infographic_path)
        else:
            section["infographic_base64"] = None

    html = template.render(
        title=content.get("title", "Newsletter"),
        eyebrow=content.get("eyebrow", "Intelligence Brief"),
        subject=content.get("title", "Newsletter"),
        date=date,
        answer_summary=content.get("answer_summary", ""),
        sections=sections,
        sources=content.get("sources", []),
        logo_base64=logo_base64,
        sender_email=cfg.newsletter().get("sender_email", ""),
    )

    # Inline all CSS for email client compatibility
    html = transform(
        html,
        base_url=None,
        remove_classes=False,
        strip_important=False,
    )

    output_path.write_text(html, encoding="utf-8")
    size_kb = output_path.stat().st_size / 1024
    print(f"Rendered newsletter to {output_path} ({size_kb:.1f} KB)")

    if size_kb > 90:
        print(
            f"WARNING: Newsletter is {size_kb:.1f} KB. "
            "Gmail clips emails over 102 KB — consider reducing infographic sizes."
        )

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render newsletter HTML from content JSON")
    parser.add_argument("--content", required=True, help="Path to content JSON file")
    parser.add_argument("--output", default=None, help="Output HTML path (optional)")
    args = parser.parse_args()

    content_path = Path(args.content)
    if not content_path.exists():
        print(f"ERROR: Content file not found: {content_path}")
        sys.exit(1)

    content = json.loads(content_path.read_text(encoding="utf-8"))

    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = TMP_DIR / f"newsletter_{date_str}.html"

    render(content, output_path)
    print(f"\nOpen in browser to preview: file:///{output_path.resolve()}")
