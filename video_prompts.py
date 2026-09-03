from __future__ import annotations

import argparse
import os
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

    return f"""You are a short-form shitpost comedy director creating a video-generation-ready script from the draft below.

IMPORTANT: Write for an AI VIDEO GENERATOR, not for a human screenwriter. The comedy must be expressed through visible actions, physical reactions, environments, camera shots, and timing. Do not merely describe what the character says.

The finished concept should work as a 20-45 second vertical 9:16 video. Preserve the core joke, but you MAY rewrite the spoken dialogue when necessary to make it fit the visual sequence. Keep the joke simple, coherent, and easy to generate.

DRAFT
HOOK:
{read('hook.txt')}

PREMISE:
{read('premise.txt')}

ORIGINAL SCRIPT:
{read('script.txt')}

EXISTING VISUAL NOTES:
{read('visuals.txt')}

CHARACTER SYSTEM
Use recognizable internet shitpost character archetypes when they genuinely improve the joke. Possible recurring characters include:
- Chud-style Wojak: exaggerated confident/rough internet-guy appearance
- Doomer-style Wojak: tired, defeated, bleak expression
- NPC-style Wojak: blank, repetitive, emotionally vacant behavior
- Soyjak-style character: exaggerated shocked/excited reaction
- Bloomer-style character: optimistic, functional contrast to the main character
- generic normie: ordinary person who reacts to the absurd internet character
- terminally-online gamer
- unemployed bedroom dweller
- overconfident crypto/memecoin bro

These are character ARCHETYPES, not exact copies of a particular artist's image. Use an original visual interpretation suitable for the scene. Do not use copyrighted franchise characters.

Choose 1-3 characters maximum. Do not add characters just for decoration. Every character must have a comedic purpose.

VISUAL-FIRST WRITING RULES
1. Establish the main character, location, clothing, important props, and time of day in the first shot.
2. Create a CONTINUITY STATE and maintain it throughout the entire video.
3. If a character starts using a desktop PC, every later computer interaction must use that same desktop PC unless the script explicitly shows a transition to another device.
4. Never spontaneously introduce a laptop, phone, tablet, different room, different clothing, new furniture, or replacement prop.
5. Do not teleport characters or objects between shots.
6. Keep faces, body type, clothing, hairstyle, room layout, lighting, props, and screen position consistent.
7. Every shot must have a visible action. Avoid static shots where nothing happens.
8. Write physical comedy and facial reactions into the action rather than relying on narration.
9. Use visual escalation: normal situation -> specific absurd detail -> escalation -> strongest visual punchline.
10. The final shot must visually reinforce the joke's final line or realization.
11. Prefer mundane settings exaggerated into absurd situations: bedroom, gaming desk, job-search screen, kitchen, supermarket, bus stop, workplace, etc.
12. Crypto/memecoin references should be part of the joke's world, not advertisements or financial advice.
13. Do not write generic influencer/TikTok language, listicles, motivational content, product promotion, or crypto recommendations.
14. Do not copy existing memes, jokes, distinctive catchphrases, or recognizable copyrighted characters.

CONTINUITY STATE
Before writing the shots, silently establish:
- character appearance
- clothing
- location
- time of day
- lighting
- important props
- exact computer/device being used
- position of important objects
- visual style
Then keep these unchanged unless the script explicitly requires a change.

VIDEO SCRIPT FORMAT
Write the result as a sequence of 4-8 shots. Each shot must contain:
SHOT X — duration
VISUAL: exactly what is visible and what the characters physically do.
CAMERA: framing and movement.
DIALOGUE/VO: spoken words, if any.
SOUND: important sound effects or environmental audio.

The dialogue should be short and natural. Let the visuals carry as much of the joke as possible.

After the shots, include:

CHARACTER BIBLE:
A concise description of each character's appearance, personality, clothing, and recurring visual traits so an AI video generator can keep them consistent.

CONTINUITY LOCK:
A concise list of the location, props, device, clothing, lighting, and other details that MUST remain consistent across shots.

MASTER VIDEO PROMPT:
One polished prompt suitable for pasting into an AI video generator. It must describe the complete visual concept, characters, setting, action progression, camera language, comedic tone, 9:16 framing, continuity, and final punchline.

NEGATIVE PROMPT:
Include continuity errors, changing faces, changing clothes, extra characters, duplicate characters, disappearing props, device changes, room changes, text artifacts, malformed hands, extra limbs, watermarks, logos, random cinematic effects, and anything that weakens the joke.

EDITING NOTES:
Give concise instructions for cuts, pacing, caption placement, pauses, sound effects, and punchline timing.

Do NOT include affiliate links, monetization instructions, financial advice, or automatic posting instructions.
"""


def generate_for(folder: Path) -> None:
    output = ollama(build_prompt(folder))
    (folder / "master_video_prompt.txt").write_text(output, encoding="utf-8")
    print(f"Created AI video package: {folder / 'master_video_prompt.txt'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create AI-video-ready scripts and prompt packages")
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
