"""Send a message to the team's Google Chat space (incoming webhook). Dev only.

    uv run python -m scripts.devfree.notify "public_test 100/1000, ETA 16:00"

GOOGLE_WEBHOOK_URL comes from the environment or .env. The URL holds the space's key: keep it in
.env (gitignored), never in code, logs or the pod.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def webhook_url() -> str:
    url = os.environ.get("GOOGLE_WEBHOOK_URL", "")
    env = ROOT / ".env"
    if not url and env.is_file():
        for line in env.read_text().splitlines():
            if line.startswith("GOOGLE_WEBHOOK_URL="):
                url = line.split("=", 1)[1].strip().strip('"')
    if not url:
        raise SystemExit("GOOGLE_WEBHOOK_URL is not set")
    return url


def send(text: str) -> int:
    request = urllib.request.Request(
        webhook_url(),
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json; charset=UTF-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status


def main(argv: list[str] | None = None) -> int:
    text = " ".join(argv if argv is not None else sys.argv[1:]).strip()
    if not text:
        raise SystemExit("usage: python -m scripts.devfree.notify MESSAGE")
    status = send(text)
    print(f"sent ({status})")
    return 0 if status == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
