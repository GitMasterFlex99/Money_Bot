from __future__ import annotations

import argparse
import os
import random
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "content"))

THEMES = [
    "NEET / unemployment absurdity",
    "Chud / Gigachad internet behavior",
    "Doomer / bleak internet behavior",
    "gaming / terminally-online gamer behavior",
    "being broke / financial desperation played for comedy",
    "wizardposting / wizardmaxxing",
    "absurd everyday situation",
    "terminally-online social behavior",
    "crypto / memecoin culture as a joke",
    "normie versus bizarre internet creature",
    "ridiculous overreaction to a tiny problem",
    "cursed maxxing / mode-posting concept",
]


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
        list(CONTENT_DIR.rglob("script.txt")) + list(CONTENT_DIR.rglob("*_script.txt")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    folders: list[Path] = []
    seen: set[Path] = set()
    for script in scripts:
        if script.parent not in seen:
            folders.append(script.parent)
            seen.add(script.parent)
        if len(folders) >= limit:
            break
    return folders


def build_prompt(folder: Path) -> str:
    def read(name: str) -> str:
        candidates = [folder / name, folder / f"{folder.name}_{name}"]
        for path in candidates:
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
        matches = sorted(folder.glob(f"*_{name}")) + sorted(folder.glob(f"*_{name}.txt"))
        for path in matches:
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()
        return ""

    selected_theme = random.choice(THEMES)
    source_hook = read("hook.txt")
    source_premise = read("premise.txt")
    source_script = read("script.txt")
    source_visuals = read("visuals.txt")

    return f"""You are the FINAL MEME DIRECTOR for a short-form shitpost account.

You are NOT a script adapter. You are an ORIGINAL MEME IDEA GENERATOR that happens to receive an old content draft as background reference.

The old draft is deliberately isolated below. You MUST NOT rewrite it, continue it, summarize it, or preserve its story. Use it only to understand broad comedy territory if useful.

RANDOM CREATIVE MODE
The program randomly selected this flavor for THIS video:
{selected_theme}

This selected theme is the PRIMARY creative instruction. Build the new joke around it.

SOURCE DRAFT — BACKGROUND REFERENCE ONLY
SOURCE HOOK:
{source_hook}

SOURCE PREMISE:
{source_premise}

SOURCE SCRIPT:
{source_script}

SOURCE VISUALS:
{source_visuals}

SOURCE ISOLATION RULE
Treat everything above as a discarded old draft sitting in a reference folder. Your new video should work even if the source text is deleted completely.

DO NOT:
- reuse the source's dialogue
- continue the source's story
- preserve its sequence of events
- preserve its main object merely because it appears there
- preserve its brand, website, device, location, or character unless independently useful
- turn the old script into a shorter version
- paraphrase the old script
- make an eBay/ThinkPad/computer resale joke merely because the source mentions those things

If the source and your new concept have the same central premise, THROW YOUR CONCEPT AWAY AND MAKE ANOTHER ONE.

CREATIVE PRIORITY
1. RANDOMLY SELECTED THEME
2. ORIGINAL VISUAL GAG
3. IMMEDIATE PREMISE
4. CONCRETE VISUAL PUNCHLINE
5. MEME TIMING
6. STYLIZED ANIMATION
7. CONTINUITY
8. SOURCE REFERENCE — LAST PRIORITY

THIS IS A MEME, NOT A STORY
Create a 6-12 second visual shitpost. It should feel like a bizarre internet image suddenly came to life.

Think in this structure:
SETUP IMAGE -> ONE STUPID ESCALATION -> UNEXPECTED VISUAL REVEAL -> CUT

Do not write a conventional narrative with exposition, dialogue, emotional arc, or multiple story beats.

VISUAL PUNCHLINE — NON-NEGOTIABLE
The final shot MUST physically show the joke's consequence, reveal, reversal, failure, or absurd result.

GOOD:
- character thinks an object is valuable; reveal shows it is worthless
- character performs an absurdly serious ritual; the result is pathetic
- character activates something confidently; something ridiculous immediately happens
- character opens something expecting one thing; completely different thing is inside
- tiny everyday inconvenience causes an absurdly disproportionate physical response
- character finally achieves the goal; the result is obviously useless

BAD:
- character looks sad
- character looks angry
- character looks embarrassed
- character stares at camera
- character sighs
- generic zoom on face
- narrator explains the joke
- caption tells the audience what they should find funny

HARD RULE: If the final shot could be replaced with "character reacts" and the joke still works, the concept is INVALID. Regenerate it.

The reveal should preferably be visible without readable AI-generated text. If text is important, put it in CAPTION TEXT for editing rather than relying on generated lettering.

STYLE
Broad internet shitpost energy: NEET, Chud, Doomer, wizardposting, gaming, broke-life, terminally-online behavior, cursed maxxing, occasional crypto/memecoin jokes.

Use these as loose archetypes, not exact characters. Do not copy any particular account, artist, meme image, joke, punchline, or distinctive phrase.

VISUAL LANGUAGE
- stylized 2D, 2.5D, simple 3D, or low-poly
- exaggerated faces
- readable silhouettes
- cheap/simple environments
- awkward or stiff movement
- sudden physical escalation
- blunt framing
- fast hard cuts
- 9:16 vertical
- no photorealism
- no Hollywood cinematography
- no commercial polish

SLANG
Use slang only when it makes the joke better: maxxing, locked in, bro, cooked, mode, it's over, we are so back, wizardmaxxing, etc. Do not force slang into every line.

WIZARDPOSTING
Wizardposting is only one possible theme. Do not insert magic unless the randomly selected theme calls for it or the idea genuinely benefits from it.

CORE RULES
1. ONE central gag.
2. 6-12 seconds total.
3. 1-4 shots maximum.
4. Start immediately on the funny situation.
5. Every shot contains visible action.
6. Zero dialogue is preferred when the visual gag works without it.
7. If dialogue is used, maximum two very short lines.
8. Final shot contains the actual reveal/consequence, NOT merely a reaction.
9. Never explain the joke.
10. Keep props and characters consistent.
11. If a desktop PC appears, it remains the same desktop PC.
12. Never randomly switch devices, clothing, rooms, or object positions.
13. Captions are added during editing.
14. Crypto is comedy only, never financial advice or token promotion.

CHARACTER ARCHETYPES
Use original interpretations of:
- Chud-style internet guy
- Doomer-style internet guy
- Gigachad-style character
- unemployed bedroom dweller
- terminally-online gamer
- overconfident crypto bro
- wizard/wizardposter
- generic normie/wagie
- absurd internet creature

CONTINUITY LOCK
Silently establish exact appearance, clothing, location, lighting, important props, device, object positions, and animation style. Keep them consistent across every shot.

OUTPUT FORMAT — FOLLOW EXACTLY
Return ONLY these sections:

CONCEPT:
One sentence describing the NEW gag. It must not describe the source draft.

CHARACTER BIBLE:
Very concise.

CONTINUITY LOCK:
Very concise.

SHOTS:
SHOT 1 — X seconds
VISUAL: ...
CAMERA: ...
DIALOGUE/VO: ...
SOUND: ...

SHOT 2 — X seconds
VISUAL: ...
CAMERA: ...
DIALOGUE/VO: ...
SOUND: ...

Add SHOT 3 and SHOT 4 only when necessary.

MASTER VIDEO PROMPT:
One compact prompt matching the SHOTS exactly. State stylized, non-photorealistic 9:16 meme animation. Do not invent additional shots or actions.

NEGATIVE PROMPT:
photorealism, realistic humans, Hollywood realism, commercial polish, long cinematic pacing, changing faces, changing clothes, extra characters, duplicate characters, disappearing props, device changes, room changes, teleporting objects, unreadable AI-generated text, malformed hands, extra limbs, watermarks, logos, random cinematic effects, unnecessary camera movement

CAPTION TEXT:
Only short captions for editing.

VOICEOVER:
NONE unless genuinely necessary.

EDITING NOTES:
Hard cuts, exact pacing, caption timing, sound effects, and punchline timing.

FINAL REJECTION TEST
Silently reject and regenerate before answering if ANY apply:
- The new idea is recognizably the old script with details changed.
- The source's central premise is still driving the joke.
- The source's dialogue was reused or paraphrased.
- The source's main object is retained without an independent comedic reason.
- The result is longer than 12 seconds.
- More than 4 shots are needed.
- There is more than one central joke.
- The final shot is only a facial reaction.
- There is no concrete visual reveal, reversal, failure, or absurd consequence.
- It needs explanatory narration to be funny.
- It resembles an advertisement, short film, tutorial, explainer, or conventional skit.
- It is photorealistic.

Do NOT include affiliate links, monetization instructions, financial advice, or automatic posting instructions.
"""


def generate_for(folder: Path) -> None:
    output = ollama(build_prompt(folder))
    output_path = folder / f"{folder.name}_video_prompt.txt"
    output_path.write_text(output, encoding="utf-8")
    print(f"Created AI video package: {output_path}")


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
