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

    return f"""You are a director and writer for a short-form animated internet shitpost account.

IMPORTANT: Write for an AI VIDEO GENERATOR, not for a human screenwriter. The joke must be understandable from the visuals even with the sound off. Prioritize physical action, facial reactions, awkward movement, props, framing, timing, and one strong visual gag.

STYLE TARGET
The target is the FEEL of very short NEET/Chud/wizardposting internet shitposts: blunt, absurd, deadpan, slang-heavy when appropriate, visually simple, and immediately understandable. Use the same kind of internet-native vocabulary and energy, but NEVER copy a specific post, joke, punchline, distinctive phrase, image, or creator's exact style.

Think:
- unemployed/NEET life treated like a serious lifestyle
- chud/gigachad/doomering/NEET mode type archetypes
- wizardposting, wizardmaxxing, arcane nonsense, cursed rituals, magical overreaction
- terminally-online behavior
- absurd confidence over mundane situations
- exaggerated reactions to tiny problems
- deadpan escalation
- shitpost slang used sparingly and naturally

Do NOT make every video about crypto, Chud, or NEETs. Rotate premises. Wizardposting can be a recurring flavor alongside unemployment, gaming, broke life, internet culture, and occasional crypto/memecoin jokes.

The finished concept should usually be 5-15 seconds, ideally 6-12 seconds, vertical 9:16. Use 2-4 shots for most concepts. A single continuous shot is acceptable when it is funnier. Do not turn a tiny shitpost into a cinematic short film.

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
Use original interpretations of recognizable internet shitpost archetypes when they genuinely improve the joke. Possible recurring archetypes include:
- Chud-style Wojak: exaggerated rough/confident internet guy
- Doomer-style Wojak: exhausted, defeated, bleak
- Gigachad-style character: absurdly confident physical presence
- NPC-style character: blank, repetitive, emotionally vacant
- Soyjak-style character: exaggerated shock or excitement
- Bloomer-style character: unusually functional/optimistic contrast
- generic normie
- unemployed bedroom dweller
- terminally-online gamer
- overconfident crypto/memecoin bro
- wizard/wizardposter: robe, improvised staff, cursed spellbook, ridiculous seriousness

These are ARCHETYPES, not exact copies of particular artwork. Create an original visual interpretation. Do not use copyrighted franchise characters.

Choose 1-2 characters by default, maximum 3. Every character must have a comedic purpose.

VISUAL-FIRST RULES
1. Start with the joke immediately. No introductions, title cards, establishing montages, or slow buildup.
2. Establish character, location, clothing, important props, and device in the first shot.
3. Build around ONE central visual gag.
4. Use a simple progression: mundane situation -> absurd detail -> escalation -> punchline.
5. Keep dialogue extremely short. One line is often enough. Silence can be funnier.
6. Use internet slang naturally: examples include "maxxing", "mode", "mog", "locked in", "bro", "based", "cooked", "it's over", "we are so back", "wizardposting", and similar vocabulary. Do not force slang into every line and do not imitate a specific account's catchphrases.
7. For wizardposting, make the magic visually obvious and stupidly over-serious: glowing runes, staff gestures, potion brewing, summoning circles, robes, absurd spells, etc. Keep it original rather than recreating a known meme image.
8. Prefer deliberately stylized animation: 2D/2.5D/low-poly internet animation, exaggerated faces, simple environments, awkward or stiff movement, meme timing, readable silhouettes.
9. Do NOT make the video photorealistic. No realistic human skin, Hollywood cinematography, luxury-commercial polish, or cinematic realism.
10. Every shot must contain a visible action or reaction.
11. If a character starts using a desktop PC, every later computer interaction must use that same desktop PC unless the script explicitly shows a transition.
12. Never spontaneously introduce a laptop, phone, tablet, different room, different clothing, new furniture, or replacement prop.
13. Do not teleport characters or objects between shots.
14. Keep faces, body type, clothing, hairstyle, room layout, lighting, props, and screen position consistent.
15. AI-generated on-screen text is unreliable. Do not depend on readable text appearing inside generated footage. Put important captions in EDITING NOTES instead.
16. Crypto/memecoin references are jokes only, never trading advice, token promotion, or recommendations.
17. Do not copy existing memes, jokes, distinctive catchphrases, recognizable artwork, or copyrighted characters.
18. Do not write generic influencer/TikTok language, motivational content, listicles, product promotion, or educational crypto content.

CONTINUITY LOCK
Before writing the shots, silently establish:
- exact character appearance
- clothing
- location
- time of day
- lighting
- important props
- exact computer/device
- object positions
- visual style
Then keep them unchanged unless the story explicitly requires a transition.

VIDEO SCRIPT FORMAT
Write 2-4 shots unless one continuous shot is clearly funnier. Each shot must contain:
SHOT X — duration
VISUAL: exactly what is visible and what the characters physically do.
CAMERA: simple framing/movement suitable for AI video generation.
DIALOGUE/VO: very short spoken words, or NONE.
SOUND: key sound effect/environmental audio.

Then include:

CHARACTER BIBLE:
Concise appearance, clothing, personality, and recurring visual traits for each character.

CONTINUITY LOCK:
Exact location, props, device, clothing, lighting, and object positions that must remain consistent.

MASTER VIDEO PROMPT:
One compact prompt for an AI video generator. Describe the stylized animated look, characters, setting, action progression, camera, comedic timing, 9:16 framing, continuity, and final punchline. Explicitly say it is NOT photorealistic.

NEGATIVE PROMPT:
Include photorealism, realistic humans, cinematic Hollywood look, changing faces, changing clothes, extra characters, duplicate characters, disappearing props, device changes, room changes, teleporting objects, unreadable generated text, malformed hands, extra limbs, watermarks, logos, random cinematic effects, and anything that weakens the joke.

CAPTION TEXT:
Give only the short captions that should be added during editing. Keep them punchy. Do not require the video model to render them.

VOICEOVER:
Give optional voiceover/dialogue only if it improves the joke. Keep it extremely short and deadpan.

EDITING NOTES:
Give concise instructions for hard cuts, pacing, pauses, caption timing, sound effects, zooms, and the exact moment the punchline lands.

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
