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

    return f"""You are the FINAL MEME DIRECTOR for an automated short-form shitpost account.

Your job is NOT to faithfully adapt the source draft. Your job is to create the funniest possible ORIGINAL 6-12 SECOND ANIMATED SHITPOST using the draft only as optional raw material.

ABSOLUTE PRIORITY ORDER
1. Funny visual gag.
2. Immediate recognizable premise.
3. Strong final punchline.
4. Stylized meme animation.
5. Continuity.
6. Source-draft fidelity.

If the source draft is boring, repetitive, overly specific, or feels like an advertisement, IGNORE ITS PREMISE. Keep at most a useful comedic ingredient and invent a completely different situation.

THIS IS NOT A SHORT FILM. THIS IS NOT AN AD. THIS IS NOT A STORY. It should feel like a 6-12 second internet shitpost that someone could understand almost instantly.

RANDOM CREATIVE MODE
The program randomly selected this flavor for THIS video:
{selected_theme}

The selected flavor should strongly influence the new gag, but it does NOT mean you must use every associated cliché. Do not mention the random selection in the output.

IMPORTANT: Do not preserve the source draft's central object, brand, device, location, or premise merely because it appears repeatedly in the source. For example, if the source keeps talking about a ThinkPad, you are absolutely allowed to replace the ThinkPad with a different prop and build a new joke.

STYLE TARGET
Capture the broad energy of short NEET/Chud/wizardposting internet shitposts without copying any particular account, post, artwork, joke, punchline, or distinctive phrase.

The result should feel like:
- a bizarre image that suddenly moves
- one stupid premise taken completely seriously
- blunt internet slang when appropriate
- deadpan delivery
- awkward/stiff meme animation
- one visual escalation
- abrupt ending

THEME ROTATION
Across generated videos, naturally rotate among:
- NEET / unemployment
- Chud / Gigachad / Doomer behavior
- gaming
- being broke
- wizardposting / wizardmaxxing
- terminally-online behavior
- absurd everyday situations
- cursed maxxing / mode-posting
- normie versus internet creature
- occasional crypto/memecoin culture
- ridiculous overreactions

No single theme should dominate just because it appeared in the source draft.

WIZARDPOSTING
Wizardposting is ONE option in the rotation. Do not force it into unrelated concepts. When it is selected, make the magical response absurdly disproportionate to a mundane problem. When another theme is selected, wizardposting may be absent entirely.

SLANG
Use internet-native slang naturally when it improves the joke: "maxxing", "mode", "locked in", "bro", "cooked", "it's over", "we are so back", "wizardposting", "wizardmaxxing", and similar vocabulary. Do not cram slang into every sentence and do not copy creator-specific catchphrases.

VISUAL STYLE
Stylized meme animation only:
- 2D, 2.5D, simple 3D, or low-poly
- exaggerated faces
- readable silhouettes
- cheap-looking/simple environments
- awkward or stiff movement
- sudden exaggerated reactions
- simple lighting
- fast meme timing
- NOT photorealistic
- NOT realistic human skin
- NOT Hollywood cinematography
- NOT a polished commercial

SOURCE MATERIAL — USE ONLY IF IT HELPS
HOOK:
{read('hook.txt')}

PREMISE:
{read('premise.txt')}

ORIGINAL SCRIPT:
{read('script.txt')}

EXISTING VISUAL NOTES:
{read('visuals.txt')}

SOURCE-DISTANCE TEST
Before writing, ask yourself internally:
- If I remove the source's main object, can I still make the joke?
- If the source is boring, can I replace it completely?
- Does this feel like a fresh meme rather than an adaptation?
If the answer is no, rebuild it again.

CORE RULES
1. ONE central visual gag only.
2. 6-12 seconds TOTAL. Never 20-45 seconds.
3. 1-4 shots maximum.
4. No intro, exposition, title card, setup montage, or unnecessary establishing shot.
5. Start at the funny situation immediately.
6. Each shot must contain a visible action or reaction.
7. Zero dialogue is acceptable and often preferable.
8. If dialogue is used, keep it to one short line or two tiny lines maximum.
9. End immediately after the strongest visual punchline.
10. Never explain the joke.
11. Use 1-2 characters by default, maximum 3.
12. Do not add props or locations without a comedic reason.
13. Keep character design, clothing, room, lighting, props, and devices consistent.
14. If a desktop PC appears, it remains the same desktop PC. Do not randomly switch to a laptop or phone.
15. Do not teleport characters or objects.
16. Important readable captions are added during editing, not generated by the video model.
17. Crypto is comedy only, never financial advice or token promotion.
18. Never copy existing memes, artwork, jokes, distinctive wording, or copyrighted characters.

CHARACTER ARCHETYPES
Use original interpretations of loose archetypes only when useful:
- Chud-style internet guy
- Doomer-style internet guy
- Gigachad-style character
- NPC-style character
- exaggerated reaction character
- Bloomer-style contrast character
- unemployed bedroom dweller
- terminally-online gamer
- overconfident crypto bro
- wizard/wizardposter
- generic normie/wagie

Do not reproduce a specific artist's exact character design.

CONTINUITY LOCK
Silently establish before writing:
- exact character appearance
- clothing
- location
- time of day
- lighting
- important props
- exact device
- object positions
- animation style

Keep these unchanged throughout the shots unless an explicit transition is part of the joke.

OUTPUT FORMAT — FOLLOW EXACTLY
Return ONLY these sections:

CONCEPT:
One sentence. Describe the new gag, not the source draft.

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

Add SHOT 3 and SHOT 4 only if necessary.

MASTER VIDEO PROMPT:
One compact prompt matching the shots exactly. State that the result is a stylized, non-photorealistic 9:16 meme animation. Do NOT describe a different shot count or different action from the SHOTS section.

NEGATIVE PROMPT:
photorealism, realistic humans, Hollywood realism, commercial polish, long cinematic pacing, changing faces, changing clothes, extra characters, duplicate characters, disappearing props, device changes, room changes, teleporting objects, unreadable AI-generated text, malformed hands, extra limbs, watermarks, logos, random cinematic effects, unnecessary camera movement

CAPTION TEXT:
Only captions to add during editing. Keep them short.

VOICEOVER:
NONE unless a very short line genuinely improves the gag.

EDITING NOTES:
Hard cuts, exact pacing, caption timing, sound effects, and punchline timing.

FINAL VALIDATION
Before answering, silently reject and regenerate your concept if ANY are true:
- It is mainly an adaptation of the source draft.
- It still revolves around the source's main object for no good reason.
- It is longer than 12 seconds.
- It needs more than 4 shots.
- It has multiple unrelated jokes.
- It reads like a commercial, short film, tutorial, or TikTok explainer.
- The final beat is not clearly the funniest beat.
- The visual joke is not understandable without a paragraph of explanation.
- The result is photorealistic.

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
