from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
DB_PATH = Path(os.getenv("DB_PATH", "money_bot.db"))
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "content"))
DISCLOSURE = os.getenv(
    "AFFILIATE_DISCLOSURE",
    "This post contains affiliate links. I may earn a commission if you buy through my link.",
)

# Conservative defaults. These are guardrails, not a guarantee of platform compliance.
BLOCKED_PATTERNS = [
    r"guaranteed?\s+(income|money|profit|returns?|results?)",
    r"guaranteed?\s+to\s+(make|earn)",
    r"get\s+rich\s+quick",
    r"risk[- ]free",
    r"100%\s+(guaranteed|safe|effective)",
    r"cure[sd]?\s+(cancer|depression|anxiety|diabetes)",
    r"doctor[- ]approved",
    r"financial\s+advice",
    r"insider\s+tip",
    r"like\s+for\s+like",
    r"follow\s+for\s+follow",
    r"comment\s+.{0,20}\s+and\s+win",
    r"pretend\s+to\s+be",
]


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            niche TEXT NOT NULL,
            product TEXT,
            status TEXT NOT NULL,
            script TEXT NOT NULL,
            caption TEXT NOT NULL,
            flags TEXT NOT NULL
        )"""
    )
    return conn


def load_config():
    path = Path("config.json")
    if not path.exists():
        raise SystemExit("config.json not found")
    return json.loads(path.read_text(encoding="utf-8"))


def safety_scan(text: str) -> list[str]:
    flags = []
    lowered = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            flags.append(pattern)
    return flags


def prompt_for(cfg: dict, product: dict | None) -> str:
    product_block = "No specific product; create a useful niche post."
    if product:
        product_block = (
            f"Product: {product.get('name', '')}\n"
            f"Affiliate URL: {product.get('url', '')}\n"
            f"Verified facts: {product.get('facts', [])}"
        )
    return f"""You are the content writer for a small affiliate creator.

Niche: {cfg.get('niche')}
Audience: {cfg.get('audience')}
Platform: {cfg.get('platform')}
Tone: {cfg.get('tone')}
Goal: {cfg.get('content_goal')}

{product_block}

Create ONE original short-form content package. It must provide genuine entertainment or useful information, not spam.

Rules:
- Never invent product specifications, prices, reviews, discounts, scarcity, testimonials, or personal experience.
- Never promise income, health outcomes, financial returns, or guaranteed results.
- Do not impersonate a person, company, expert, or customer.
- Do not ask viewers to manipulate likes, comments, follows, or views.
- Do not use fake urgency or fake social proof.
- If a product is included, make the recommendation proportionate and explain a concrete reason it may be useful.
- Include an explicit affiliate disclosure in the caption.
- Do not copy wording from existing creators.

Return exactly this format:
HOOK:
<one short hook>

SCRIPT:
<30-60 second spoken script>

CAPTION:
<caption with disclosure>

CTA:
<a non-manipulative CTA>
"""


def ollama_generate(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.RequestException as exc:
        raise SystemExit(f"Could not reach Ollama at {OLLAMA_URL}: {exc}") from exc


def parse_package(text: str) -> tuple[str, str, str, str]:
    sections = {}
    current = None
    for line in text.splitlines():
        match = re.match(r"^(HOOK|SCRIPT|CAPTION|CTA):\s*$", line.strip(), re.I)
        if match:
            current = match.group(1).upper()
            sections[current] = []
        elif current:
            sections[current].append(line)
    required = ["HOOK", "SCRIPT", "CAPTION", "CTA"]
    missing = [key for key in required if not "\n".join(sections.get(key, [])).strip()]
    if missing:
        raise ValueError(f"Model response missing sections: {', '.join(missing)}")
    return tuple("\n".join(sections[key]).strip() for key in required)


def save_content(cfg: dict, product: dict | None, hook: str, script: str, caption: str, cta: str, flags: list[str]):
    product_name = product.get("name") if product else None
    payload = "\n".join([hook, script, caption, cta])
    content_hash = hashlib.sha256(payload.lower().encode("utf-8")).hexdigest()

    conn = db()
    existing = conn.execute("SELECT id FROM content WHERE content_hash = ?", (content_hash,)).fetchone()
    if existing:
        conn.close()
        return None, "duplicate"

    status = "review" if flags else "review"
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO content(content_hash, created_at, niche, product, status, script, caption, flags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (content_hash, now, cfg.get("niche", ""), product_name, status, script, caption, json.dumps(flags)),
    )
    conn.commit()
    conn.close()

    folder = CONTENT_DIR / datetime.now().strftime("%Y-%m-%d") / content_hash[:8]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "hook.txt").write_text(hook, encoding="utf-8")
    (folder / "script.txt").write_text(script, encoding="utf-8")
    (folder / "caption.txt").write_text(caption, encoding="utf-8")
    (folder / "cta.txt").write_text(cta, encoding="utf-8")
    (folder / "review.json").write_text(
        json.dumps({"status": status, "flags": flags, "product": product_name}, indent=2),
        encoding="utf-8",
    )
    return folder, "created"


def generate():
    cfg = load_config()
    products = cfg.get("affiliate_products") or [None]
    limit = max(1, min(int(cfg.get("max_posts_per_run", 3)), 5))
    created = 0

    for product in products[:limit]:
        raw = ollama_generate(prompt_for(cfg, product))
        try:
            hook, script, caption, cta = parse_package(raw)
        except ValueError as exc:
            print(f"Skipped malformed model output: {exc}")
            continue

        if DISCLOSURE.lower() not in caption.lower():
            caption = f"{caption.rstrip()}\n\n{DISCLOSURE}"

        combined = "\n".join([hook, script, caption, cta])
        flags = safety_scan(combined)
        folder, result = save_content(cfg, product, hook, script, caption, cta, flags)
        if result == "duplicate":
            print("Skipped duplicate draft.")
            continue
        created += 1
        print(f"Created review draft: {folder}")
        if flags:
            print("  SAFETY FLAGS: manual review required")

    print(f"Done. Created {created} draft(s). Nothing was published automatically.")


def init():
    db().close()
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Initialized database: {DB_PATH}")
    print(f"Content directory: {CONTENT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Money Bot affiliate content assistant")
    parser.add_argument("command", choices=["init", "generate"])
    args = parser.parse_args()
    if args.command == "init":
        init()
    else:
        generate()
