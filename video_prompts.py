from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "content"))


def ollama(prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def latest_drafts(limit: int = 3) -> list[Path]:
    scripts = sorted(
        CONTENT_DIR.rglob("script.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [p.parent for p in scripts[:limit]]


def build_prompt(folder: Path) -> str:
    def read(name: str) -> str:
        path = folder / name
        return path.read_text(encoding="utf-8").strip() if path.exists() else ""

    return f"""Turn this short-form comedy draft into a production-ready prompt package for an AI video generator such as Sora, Veo, Kling, Runway, or similar.

The goal is NOT to rewrite the joke. Preserve the exact comedic premise and spoken script while designing visuals that make the joke work as a short vertical video.

DRAFT
HOOK:
{read('hook.txt')}

PREMISE:
{read('premise.txt')}

SCRIPT:
{read('script.txt')}

EXISTING VISUAL NOTES:
{read('visuals.txt')}

Create a coherent 20-45 second video. Use 9:16 vertical framing. Prefer 4-8 short shots rather than one complicated continuous scene. Keep the same character, room, clothing, props, lighting, and visual style consistent between shots.

STYLE
- grounded internet-native comedy
- believable live-action look unless the premise clearly benefits from animation
- slightly exaggerated facial reactions and physical comedy
- ordinary bedroom, apartment, gaming setup, workplace, street, or other setting appropriate to the script
- no logos, brands, watermarks, fake social-media UI, or copyrighted characters
- no cinematic action-movie excess unless the joke specifically calls for it
- visuals should escalate with the spoken joke and land on the final punchline
- leave clean space for captions/subtitles

Return ONLY these sections:

MASTER VIDEO PROMPT:
One detailed prompt that can be pasted into an AI video generator to create the whole video. Include subject, environment, camera, movement, lighting, continuity, pacing, performance, vertical 9:16 framing, and the comedic tone.

SHOT LIST:
Number 4-8 shots. For each shot give approximate duration, what is visible, camera framing/movement, character action/expression, and which script line it supports.

NEGATIVE PROMPT:
A concise list of things to avoid: text artifacts, extra fingers/limbs, inconsistent faces, changing clothes, changing room layout, unwanted logos, watermarks, random objects, visual glitches, exaggerated cinematic effects, and anything that would undermine the joke.

EDITING NOTES:
Give concise instructions for pacing, hard cuts, captions, sound effects, pauses, and where the final punchline should land.

VOICEOVER:
Return the spoken script exactly as supplied, with no rewriting.
"""


def generate_for(folder: Path) -> None:
    output = ollama(build_prompt(folder))
    (folder / "master_video_prompt.txt").write_text(output, encoding="utf-8")
    print(f"Created AI video package: {folder / 'master_video_prompt.txt'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create AI-video-ready prompt packages from Money Bot drafts")
    parser.add_argument("--limit", type=int, default=3, help="number of latest drafts to process")
    parser.add_argument("--folder", type=Path, help="process one specific draft folder")
    args = parser.parse_args()

    folders = [args.folder] if args.folder else latest_drafts(max(1, min(args.limit, 10)))
    if not folders:
        raise SystemExit("No drafts found. Run: python money_bot.py generate")

    for folder in folders:
        try:
            generate_for(folder)
        except requests.RequestException as exc:
            print(f"Skipped {folder}: could not reach Ollama: {exc}")
        except OSError as exc:
            print(f"Skipped {folder}: {exc}")

    print("Done. No video was published or uploaded automatically.")


if __name__ == "__main__":
    main()
