from __future__ import annotations

import argparse
import os
import random
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "content"))
MAX_ATTEMPTS = 3

# Video concepts are deliberately split into independent visual worlds.
VIDEO_STYLES = {
    "WOJAK_SHITPOST": {
        "themes": [
            "NEET / unemployment absurdity",
            "Chud internet behavior",
            "Doomer / bleak internet behavior",
            "gaming / terminally-online behavior",
            "being broke / financial desperation played for comedy",
            "absurd everyday situation",
            "terminally-online social behavior",
            "crypto / memecoin culture as a joke",
            "normie versus bizarre internet creature",
            "ridiculous overreaction to a tiny problem",
            "cursed maxxing / mode-posting concept",
        ],
        "characters": [
            "Chudjak",
            "Doomer Wojak",
            "NPC Wojak",
            "Soyjak",
            "Bloomer Wojak",
            "classic Wojak",
            "Wojak-style normie",
        ],
        "style_rules": [
            "Use recognizable Wojak meme artwork and proportions.",
            "Chudjak must be the distinctive long-haired, glasses-wearing, heavy-set Chudjak form, not a generic beanie Wojak.",
            "NPC must be the simple grey, bald, expressionless NPC form with minimal facial features.",
            "Do not substitute one Wojak archetype for another.",
            "Keep the visual style simple, blunt, meme-like, and immediately readable.",
        ],
    },
    "DREAMCORE": {
        "themes": [
            "wizardposting / wizardmaxxing",
            "surreal dream logic",
            "uncanny empty-space encounter",
            "bizarre mystical ritual",
            "liminal everyday object behaving impossibly",
            "dreamlike transformation",
            "strange nighttime vision",
        ],
        "characters": [
            "stereotypical wizard",
        ],
        "style_rules": [
            "Dreamcore is a completely separate visual style from Wojak meme videos.",
            "The wizard is NOT a Wojak, Soyjak, Chudjak, or other Wojak variant.",
            "Use surreal, uncanny, atmospheric, dreamlike environments and imagery.",
            "The wizard may have a robe, pointed hat, staff, and exaggerated beard, but must remain a standalone dreamcore character.",
            "Do not import Wojak faces, meme proportions, or Wojak character labels into dreamcore concepts.",
        ],
    },
}


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


def extract_section(text: str, name: str) -> str:
    pattern = re.compile(
        rf"^\s*{re.escape(name)}\s*:\s*(.*?)(?=^\s*[A-Z][A-Z /_-]+\s*:|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def quality_check(output: str, source_script: str, selected_style: str, selected_character: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    upper = output.upper()

    if "CONCEPT:" not in upper or "SHOTS:" not in upper or "MASTER VIDEO PROMPT:" not in upper:
        reasons.append("missing required sections")

    shot_matches = re.findall(r"^\s*SHOT\s+\d+\s*[—-]\s*(\d+(?:\.\d+)?)\s*SECONDS?", output, re.IGNORECASE | re.MULTILINE)
    if not shot_matches:
        reasons.append("no parseable shots")
    else:
        total = sum(float(value) for value in shot_matches)
        if total > 12:
            reasons.append(f"duration is {total:g} seconds")
        if len(shot_matches) > 4:
            reasons.append("more than 4 shots")

    dialogue_lines = re.findall(r"DIALOGUE/VO:\s*(.+)", output, re.IGNORECASE)
    spoken = [line for line in dialogue_lines if line.strip().upper() not in {"NONE", "(NONE)", "SILENCE", "*SILENCE*"}]
    if len(spoken) > 1:
        reasons.append("too much dialogue")

    reaction_phrases = [
        "looks sad", "looks angry", "looks embarrassed", "stares at the camera",
        "stares into the camera", "breathes heavily", "sighs", "looks disappointed",
        "contorted in disappointment", "reacts in disappointment", "reaction shot",
    ]
    if any(phrase in output.lower() for phrase in reaction_phrases):
        reasons.append("reaction-only ending language")

    caption = extract_section(output, "CAPTION TEXT")
    if len(caption) > 60 or len(caption.split()) > 8:
        reasons.append("caption is too explanatory")

    screen_text = [
        "screen displays", "screen reads", "monitor displays", "monitor reads",
        "displays a cryptic message", "text appears on screen", "message appears on screen",
    ]
    if any(phrase in output.lower() for phrase in screen_text):
        reasons.append("depends on generated screen text")

    source_terms = {term.lower() for term in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{3,}\b", source_script)}
    concept = extract_section(output, "CONCEPT").lower()
    source_markers = {"ebay", "thinkpad", "lenovo", "listing", "parts", "resell", "sold", "auction"}
    if source_terms & source_markers & set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{3,}\b", concept)):
        reasons.append("reused old source premise markers")

    character_block = extract_section(output, "CHARACTER BIBLE").lower()
    forbidden_character_phrases = [
        "name:", "age:", "personality:", "protagonist is", "main character is",
        "toasty", "gamer character", "unemployed bedroom dweller", "overconfident crypto bro",
        "terminally-online gamer",
    ]
    if any(phrase in character_block for phrase in forbidden_character_phrases):
        reasons.append("invented custom character instead of the selected archetype")

    if selected_style == "WOJAK_SHITPOST":
        allowed_terms = ["chudjak", "chud wojak", "doomer wojak", "npc wojak", "soyjak", "soy wojak", "bloomer wojak", "classic wojak", "wojak-style normie"]
        if not any(term in character_block for term in allowed_terms):
            reasons.append("Wojak video does not use an allowed Wojak archetype")
        if "wizard" in character_block and "wojak" not in character_block:
            reasons.append("wizard incorrectly used as a Wojak character")
    else:
        if "wizard" not in character_block:
            reasons.append("dreamcore video does not use the standalone wizard character")
        if any(term in character_block for term in ["chudjak", "doomer wojak", "npc wojak", "soyjak", "bloomer wojak", "classic wojak"]):
            reasons.append("Wojak character incorrectly used in dreamcore")

    if selected_character.lower() not in character_block and selected_style == "WOJAK_SHITPOST":
        reasons.append("selected character archetype was not followed")

    return not reasons, reasons


def build_prompt(folder: Path, rejection_feedback: str = "") -> tuple[str, str, str]:
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

    selected_style = random.choice(list(VIDEO_STYLES))
    style = VIDEO_STYLES[selected_style]
    selected_theme = random.choice(style["themes"])
    selected_character = random.choice(style["characters"])
    source_hook = read("hook.txt")
    source_premise = read("premise.txt")
    source_script = read("script.txt")
    source_visuals = read("visuals.txt")

    feedback_block = ""
    if rejection_feedback:
        feedback_block = f"""

AUTOMATIC QUALITY CHECK REJECTED THE PREVIOUS ATTEMPT
Problems detected: {rejection_feedback}
You MUST make a substantially different concept that fixes every listed problem. Do not merely rewrite the rejected attempt.
"""

    style_rules = "\n".join(f"- {rule}" for rule in style["style_rules"])

    prompt = f"""You are the FINAL DIRECTOR for a short-form meme account.

You are an ORIGINAL MEME IDEA GENERATOR, not a script adapter. The old draft below is background reference only.

VIDEO STYLE — LOCKED
{selected_style}

RANDOM CREATIVE THEME — LOCKED
{selected_theme}

SELECTED CHARACTER — LOCKED
{selected_character}

STYLE RULES — ABSOLUTE
{style_rules}

CHARACTER SYSTEM SEPARATION — ABSOLUTE
There are TWO completely separate visual worlds in this project.

WORLD A — WOJAK SHITPOST
Characters are established Wojak meme archetypes only: Chudjak, Doomer Wojak, NPC Wojak, Soyjak, Bloomer Wojak, classic Wojak, or Wojak-style normie.

WORLD B — DREAMCORE
The stereotypical wizard belongs ONLY to dreamcore. The wizard is a standalone dreamcore character and is NOT a Soyjak, Chudjak, Wojak, or variant of one.

NEVER MIX THE WORLDS.
If VIDEO STYLE is WOJAK_SHITPOST, do not use a wizard.
If VIDEO STYLE is DREAMCORE, do not use Chudjak, Doomer, NPC, Soyjak, Bloomer, classic Wojak, or Wojak-style normie.
Do not describe the wizard as a Wojak.
Do not describe Chudjak as a generic beanie Wojak.
Do not describe NPC as a generic human or normal person.

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
Treat everything above as a discarded old draft. The new video must work if the source text is deleted completely.

DO NOT reuse, continue, summarize, paraphrase, or shorten the source. Do not preserve its central premise, sequence of events, dialogue, brand, website, device, location, or distinctive object merely because it appears there.
If the new concept resembles the source, throw it away and make another one.
{feedback_block}

THIS IS A SHORT MEME, NOT A STORY
Create a 6-12 second visual gag.
SETUP -> ONE ESCALATION -> VISIBLE REVEAL/CONSEQUENCE -> CUT

ONE CENTRAL GAG ONLY.
Start immediately on the funny situation.
Every shot contains visible action.
Prefer zero dialogue.
Maximum one short dialogue line if absolutely necessary.

VISUAL PUNCHLINE — NON-NEGOTIABLE
The final shot MUST physically show the joke's consequence, reveal, reversal, failure, or absurd result. A facial reaction alone is invalid.

Prefer physical reveals: objects break, transform, fail, produce the wrong result, reveal something ridiculous, or cause an absurd consequence.
Do not rely on generated computer-screen text as the primary punchline.

CAPTION RULE
Caption text is optional and should usually be 0-6 words. Never explain the joke.

STYLE RULES
- 6-12 seconds total
- 1-4 shots maximum
- 9:16 vertical
- fast hard cuts
- simple, readable visuals
- stylized rather than photorealistic
- no Hollywood cinematography
- no commercial polish
- no anime humans
- no realistic humans
- no custom original human characters
- no named original characters

WOJAK SHITPOST DIRECTION
If this is WOJAK_SHITPOST, make the chosen archetype visually recognizable and consistent across every shot. The comedy should feel like a bizarre internet meme suddenly came to life. Use NEET, unemployment, gaming, broke-life, terminally-online behavior, Chud/Doomer/Soy/NPC/Bloomer culture, and occasional crypto/memecoin jokes.

DREAMCORE DIRECTION
If this is DREAMCORE, make it atmospheric, surreal, uncanny, liminal, and dreamlike. The wizard is a standalone fantasy/dreamcore figure, not a Wojak. Use strange environments, impossible physical events, unsettling calmness, bizarre rituals, dream logic, and abrupt surreal reveals. Do not turn it into a conventional fantasy adventure or a Wojak shitpost.

WIZARDPOSTING
Wizardposting is only a dreamcore theme in this system. Never force a wizard into a Wojak shitpost.

SLANG
Use internet slang only when it naturally improves the joke. Do not force it into every concept.

CONTINUITY
Keep character appearance, clothing, environment, lighting, props, devices, and object positions consistent. Never randomly switch devices, rooms, clothing, or character types.

OUTPUT FORMAT — FOLLOW EXACTLY
Return ONLY these sections:

CONCEPT:
One sentence describing the NEW gag.

CHARACTER BIBLE:
Identify ONLY the locked character archetype and concise visual traits. Do not invent names, ages, backstories, occupations, or personalities.

CONTINUITY LOCK:
Very concise.

SHOTS:
SHOT 1 — X seconds
VISUAL: ...
CAMERA: ...
DIALOGUE/VO: NONE
SOUND: ...

SHOT 2 — X seconds
VISUAL: ...
CAMERA: ...
DIALOGUE/VO: NONE
SOUND: ...

Add SHOT 3 and SHOT 4 only when necessary.

MASTER VIDEO PROMPT:
One compact prompt matching the SHOTS exactly. Do not invent additional shots or actions.

NEGATIVE PROMPT:
photorealism, realistic humans, Hollywood realism, commercial polish, long cinematic pacing, changing faces, changing clothes, extra characters, duplicate characters, disappearing props, device changes, room changes, teleporting objects, unreadable AI-generated text, malformed hands, extra limbs, watermarks, logos, random cinematic effects, unnecessary camera movement, anime characters, realistic people, custom original human characters

CAPTION TEXT:
Only a very short optional meme caption, preferably 0-6 words. Never explain the joke.

VOICEOVER:
NONE unless absolutely necessary.

EDITING NOTES:
Hard cuts, exact pacing, caption timing, sound effects, and punchline timing.

FINAL VALIDATION
Silently reject and regenerate if ANY apply:
- Wojak and dreamcore worlds are mixed.
- A wizard appears in a WOJAK_SHITPOST video.
- A Wojak archetype appears in a DREAMCORE video.
- The wizard is described as a Wojak or Soyjak.
- Chudjak is described as a generic beanie Wojak instead of the distinctive Chudjak form.
- NPC is described as a normal human instead of the simple grey NPC form.
- The selected character is changed.
- Any human character is an unapproved custom character.
- The new idea is recognizably the old source script.
- The result is longer than 12 seconds.
- More than 4 shots are needed.
- There is more than one central joke.
- The final shot is only a facial reaction.
- The punchline depends on generated screen text.
- The caption explains the joke.
- It resembles an advertisement, tutorial, explainer, or conventional short film.
- It is photorealistic.

Do NOT include affiliate links, monetization instructions, financial advice, or automatic posting instructions.
"""
    return prompt, selected_style, selected_character


def generate_for(folder: Path) -> None:
    source_script_path = folder / "script.txt"
    if not source_script_path.exists():
        matches = sorted(folder.glob("*_script.txt"))
        source_script_path = matches[0] if matches else source_script_path
    source_script = source_script_path.read_text(encoding="utf-8") if source_script_path.exists() else ""

    last_reasons = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt, selected_style, selected_character = build_prompt(folder, last_reasons)
        output = ollama(prompt)
        valid, reasons = quality_check(output, source_script, selected_style, selected_character)
        if valid:
            output_path = folder / f"{folder.name}_video_prompt.txt"
            output_path.write_text(output, encoding="utf-8")
            print(f"Created {selected_style} video package: {output_path}")
            if attempt > 1:
                print(f"Accepted after {attempt} generation attempts.")
            return
        last_reasons = "; ".join(reasons)
        print(f"Rejected {selected_style} video prompt attempt {attempt}: {last_reasons}")

    raise RuntimeError(f"Could not produce a valid meme video prompt after {MAX_ATTEMPTS} attempts. Last problems: {last_reasons}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create separated Wojak-shitpost or dreamcore video prompt packages")
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
        except (OSError, RuntimeError) as exc:
            print(f"Skipped {folder}: {exc}")

    print("Done. No video was published or uploaded automatically.")


if __name__ == "__main__":
    main()
