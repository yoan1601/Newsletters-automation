"""
Generate an infographic image using the kie.ai REST API.
Accepts a descriptive prompt, polls for completion, downloads the PNG,
resizes it to 600px wide at 96 dpi to stay within Gmail's 102KB clip limit,
and saves it to .tmp/.

Usage:
    python tools/generate_infographic.py --prompt "Bar chart: AI adoption by industry" --name "ai_adoption"

Output: .tmp/infographic_{name}.png

API reference:
  POST https://api.kie.ai/api/v1/jobs/createTask
  GET  https://api.kie.ai/api/v1/jobs/recordInfo?taskId=<id>
"""

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

TMP_DIR = Path(".tmp")
TMP_DIR.mkdir(exist_ok=True)

KIE_API_BASE = "https://api.kie.ai"
CREATE_PATH = "/api/v1/jobs/createTask"
POLL_PATH = "/api/v1/jobs/recordInfo"
KIE_MODEL = "google/nano-banana"
MAX_POLL_SECONDS = 300
POLL_INTERVAL = 5
MAX_WIDTH_PX = 480

# Brand style suffix appended to every prompt for visual consistency
BRAND_STYLE_SUFFIX = (
    "Style: executive, minimal, systems-oriented. "
    "Color palette: Deep Navy (#0B1F3B) background or Off-White (#F8FAFC) background, "
    "Signal Green (#10B981) accent used sparingly. "
    "Prefer systems diagrams over stock imagery. "
    "Boxes = components, arrows = flows, verb labels. "
    "High whitespace, 1 idea per visual. "
    "No consumer AI imagery, no generic stock photos."
)


def generate(prompt: str, name: str) -> Path:
    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        print("ERROR: KIE_API_KEY not set in .env")
        sys.exit(1)

    full_prompt = f"{prompt}\n\n{BRAND_STYLE_SUFFIX}"
    output_path = TMP_DIR / f"infographic_{name}.jpg"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"Submitting infographic request to kie.ai (model: {KIE_MODEL})...")
    response = requests.post(
        f"{KIE_API_BASE}{CREATE_PATH}",
        headers=headers,
        json={
            "model": KIE_MODEL,
            "input": {
                "prompt": full_prompt,
                "output_format": "png",
                "image_size": "1:1",
            },
        },
        timeout=30,
    )

    if response.status_code != 200:
        print(f"ERROR: kie.ai API returned {response.status_code}: {response.text}")
        sys.exit(1)

    data = response.json()
    if data.get("code") not in (200, 0):
        print(f"ERROR: kie.ai returned error: {data}")
        sys.exit(1)

    task_id = data.get("data", {}).get("taskId")
    if not task_id:
        print(f"ERROR: No taskId in response: {data}")
        sys.exit(1)

    print(f"Task created (id: {task_id}). Polling for up to {MAX_POLL_SECONDS}s...")
    image_url = _poll(task_id, headers)
    if not image_url:
        print("ERROR: Could not retrieve image URL from kie.ai")
        sys.exit(1)

    print(f"Downloading image from: {image_url}")
    img_response = requests.get(image_url, timeout=60)
    img_response.raise_for_status()

    # Resize to max 600px wide to stay under Gmail's 102KB clip threshold
    img = Image.open(io.BytesIO(img_response.content))
    if img.width > MAX_WIDTH_PX:
        ratio = MAX_WIDTH_PX / img.width
        new_height = int(img.height * ratio)
        img = img.resize((MAX_WIDTH_PX, new_height), Image.LANCZOS)
        print(f"Resized to {MAX_WIDTH_PX}x{new_height}px")

    img = img.convert("RGB")
    img.save(str(output_path), "JPEG", quality=72, optimize=True)
    size_kb = output_path.stat().st_size / 1024
    print(f"Saved to {output_path} ({size_kb:.1f} KB)")
    return output_path


def _poll(task_id: str, headers: dict) -> str | None:
    elapsed = 0
    while elapsed < MAX_POLL_SECONDS:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        poll = requests.get(
            f"{KIE_API_BASE}{POLL_PATH}",
            headers=headers,
            params={"taskId": task_id},
            timeout=15,
        )
        if poll.status_code != 200:
            print(f"  Poll error {poll.status_code}, retrying...")
            continue

        result = poll.json()
        task_data = result.get("data", {})
        state = task_data.get("state", "")
        progress = task_data.get("progress", 0)
        print(f"  [{elapsed}s] state: {state} progress: {progress}")

        if state == "success":
            result_json_str = task_data.get("resultJson", "{}")
            try:
                result_json = json.loads(result_json_str)
            except json.JSONDecodeError:
                print(f"ERROR: Could not parse resultJson: {result_json_str}")
                return None
            urls = result_json.get("resultUrls", [])
            if urls:
                return urls[0]
            print(f"ERROR: Success state but no resultUrls: {result_json_str}")
            return None

        if state == "fail":
            print(f"ERROR: Task failed — {task_data.get('failMsg', 'unknown error')}")
            return None

    print(f"ERROR: Timed out after {MAX_POLL_SECONDS}s waiting for kie.ai task")
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an infographic via kie.ai")
    parser.add_argument("--prompt", required=True, help="Description of the infographic")
    parser.add_argument("--name", required=True, help="Short name for the output file (no spaces)")
    args = parser.parse_args()
    generate(args.prompt, args.name)
