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

# Only these recurring visual archetypes may be used as characters.
CHARACTER_ARCHETYPES = [
    "Chudjak / Chud Wojak",
    "Doomer Wojak",
    "NPC Wojak",
    "Soyjak / Soy Wojak",
    "Bloomer Wojak",
    "classic generic Wojak",
    "stereotypical wizard character",
    "Wojak-style normie",
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


def extract_section(text: str, name: str) -> str:
    pattern = re.compile(
        rf"^\s*{re.escape(name)}\s*:\s*(.*?)(?=^\s*[A-Z][A-Z /_-]+\s*:|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def quality_check(output: str, source_script: str) -> tuple[bool, list[str]]:
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

    forbidden_character_phrases = [
        "name:", "age:", "personality:", "protagonist is", "main character is",
        "toasty", "gamer character", "unemployed bedroom dweller", "overconfident crypto bro",
        "terminally-online gamer",
    ]
    character_block = extract_section(output, "CHARACTER BIBLE").lower()
    if any(phrase in character_block for phrase in forbidden_character_phrases):
        reasons.append("invented custom character instead of Wojak archetype")

    allowed_character_terms = ["wojak", "chudjak", "chud wojak", "doomer wojak", "npc wojak", "soyjak", "bloomer wojak", "wizard"]
    if character_block and not any(term in character_block for term in allowed_character_terms):
        reasons.append("character bible does not use an allowed archetype")

    return not reasons, reasons


def build_prompt(folder: Path, rejection_feedback: str = "") -> str:
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
    selected_character = random.choice(CHARACTER_ARCHETYPES)
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

    return f"""You are the FINAL MEME DIRECTOR for a short-form shitpost account.

You are NOT a script adapter. You are an ORIGINAL MEME IDEA GENERATOR that happens to receive an old content draft as background reference.

The old draft is deliberately isolated below. You MUST NOT rewrite it, continue it, summarize it, or preserve its story. Use it only to understand broad comedy territory if useful.

RANDOM CREATIVE MODE
The program randomly selected this flavor for THIS video:
{selected_theme}

RANDOM CHARACTER
The program selected this character archetype for THIS video:
{selected_character}

CHARACTER LOCK — ABSOLUTE
ALL HUMAN-LIKE CHARACTERS MUST BE WOJAK-STYLE INTERNET MEME CHARACTERS.

You MUST use the selected Wojak archetype above as the protagonist unless a second character is genuinely needed. A second character must also be one of the allowed Wojak archetypes or the stereotypical wizard.

DO NOT INVENT A NAMED ORIGINAL CHARACTER.
DO NOT GIVE THE CHARACTER A NAME, AGE, backstory, occupation-based custom identity, or personality profile.
DO NOT CREATE GENERIC ANIME PEOPLE, REALISTIC PEOPLE, CUSTOM CARTOON PEOPLE, OR NEW ORIGINAL HUMAN CHARACTERS.

The CHARACTER BIBLE should simply identify the archetype and a few visual traits, for example: "Chudjak / Chud Wojak, exaggerated muscular meme proportions, smug expression, simple meme-style clothing."

WIZARD EXCEPTION
A stereotypical wizard may be used when the random theme is wizardposting/wizardmaxxing or when a wizard is genuinely necessary for the joke. The wizard should be a simple stereotypical meme wizard: robe, pointed hat, staff, exaggerated beard. Do not invent a named fantasy character.

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
{feedback_block}

CREATIVE PRIORITY
1. RANDOMLY SELECTED THEME
2. LOCKED WOJAK CHARACTER
3. ORIGINAL VISUAL GAG
4. IMMEDIATE PREMISE
5. CONCRETE VISUAL PUNCHLINE
6. MEME TIMING
7. STYLIZED ANIMATION
8. CONTINUITY
9. SOURCE REFERENCE — LAST PRIORITY

THIS IS A MEME, NOT A STORY
Create a 6-12 second visual shitpost. It should feel like a bizarre internet image suddenly came to life.

Use this structure:
SETUP IMAGE -> ONE STUPID ESCALATION -> UNEXPECTED VISUAL REVEAL/CONSEQUENCE -> CUT

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
- a mundane object unexpectedly behaves like something completely different

BAD:
- character looks sad
- character looks angry
- character looks embarrassed
- character stares at camera
- character sighs
- generic zoom on face
- narrator explains the joke
- caption tells the audience what they should find funny
- fake computer error/message as the primary punchline

HARD RULE: If the final shot could be replaced with "character reacts" and the joke still works, the concept is INVALID. Regenerate it.

PREFER PHYSICAL REVEALS
Whenever possible, make the punchline something physically visible: an object breaks, pops, transforms, fails, reveals something ridiculous, produces the wrong result, or causes an absurd consequence. Do not rely on computer-screen text.

DIALOGUE MINIMIZATION
Prefer ZERO dialogue. The visual should carry the joke. If dialogue is necessary, use ONE short line total. Never write a speech, conversation, narration, or multiple explanatory lines.

CAPTION MINIMIZATION
CAPTION TEXT should usually be 0-6 words. It is an optional meme label, not an explanation of the joke. Good examples: "locked in", "bro is cooked", "MAXXING", "it's over", "we are so back". Do not write a sentence explaining the premise.

STYLE
Broad internet shitpost energy: NEET, Chud, Doomer, wizardposting, gaming, broke-life, terminally-online behavior, cursed maxxing, occasional crypto/memecoin jokes.

VISUAL LANGUAGE
- Wojak-style characters only
- simple meme animation
- stylized 2D, 2.5D, simple 3D, or low-poly
- exaggerated faces and silhouettes
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
6. Zero dialogue is preferred.
7. If dialogue is used, maximum ONE short line total.
8. Final shot contains the actual reveal/consequence, NOT merely a reaction.
9. Never explain the joke.
10. Only Wojak-style characters and the stereotypical wizard are permitted.
11. Never invent named characters.
12. Keep props and characters consistent.
13. If a desktop PC appears, it remains the same desktop PC.
14. Never randomly switch devices, clothing, rooms, or object positions.
15. Captions are added during editing.
16. Crypto is comedy only, never financial advice or token promotion.

CHARACTER ARCHETYPES
The ONLY permitted character types are:
- Chudjak / Chud Wojak
- Doomer Wojak
- NPC Wojak
- Soyjak / Soy Wojak
- Bloomer Wojak
- classic generic Wojak
- Wojak-style normie
- stereotypical wizard

Do not use any other human character type. Do not name characters.

CONTINUITY LOCK
Silently establish exact archetype, visual traits, clothing, location, lighting, important props, device, object positions, and animation style. Keep them consistent across every shot.

OUTPUT FORMAT — FOLLOW EXACTLY
Return ONLY these sections:

CONCEPT:
One sentence describing the NEW gag. It must not describe the source draft.

CHARACTER BIBLE:
Name ONLY the permitted archetype. Do not invent a name, age, backstory, or custom personality.

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
One compact prompt matching the SHOTS exactly. State stylized, non-photorealistic 9:16 Wojak meme animation. Do not invent additional shots or actions.

NEGATIVE PROMPT:
photorealism, realistic humans, Hollywood realism, commercial polish, long cinematic pacing, changing faces, changing clothes, extra characters, duplicate characters, disappearing props, device changes, room changes, teleporting objects, unreadable AI-generated text, malformed hands, extra limbs, watermarks, logos, random cinematic effects, unnecessary camera movement, anime characters, realistic people, custom original human characters

CAPTION TEXT:
Only a very short optional meme caption, preferably 0-6 words. Never explain the joke.

VOICEOVER:
NONE unless absolutely necessary.

EDITING NOTES:
Hard cuts, exact pacing, caption timing, sound effects, and punchline timing.

FINAL VALIDATION
Silently reject and regenerate before answering if ANY apply:
- Any human character is not a permitted Wojak archetype or stereotypical wizard.
- A character has a custom name, age, backstory, or invented identity.
- The new idea is recognizably the old script with details changed.
- The source's central premise is still driving the joke.
- The source's dialogue was reused or paraphrased.
- The result is longer than 12 seconds.
- More than 4 shots are needed.
- There is more than one central joke.
- Any shot contains a long speech or explanatory narration.
- The final shot is only a facial reaction.
- The final beat does not contain a concrete physical reveal, reversal, failure, or absurd consequence.
- The punchline depends on generated screen text.
- The caption explains the joke instead of enhancing it.
- It resembles an advertisement, short film, tutorial, explainer, or conventional skit.
- It is photorealistic.

Do NOT include affiliate links, monetization instructions, financial advice, or automatic posting instructions.
"""


def generate_for(folder: Path) -> None:
    source_script_path = folder / "script.txt"
    if not source_script_path.exists():
        matches = sorted(folder.glob("*_script.txt"))
        source_script_path = matches[0] if matches else source_script_path
    source_script = source_script_path.read_text(encoding="utf-8") if source_script_path.exists() else ""

    last_reasons = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        output = ollama(build_prompt(folder, last_reasons))
        valid, reasons = quality_check(output, source_script)
        if valid:
            output_path = folder / f"{folder.name}_video_prompt.txt"
            output_path.write_text(output, encoding="utf-8")
            print(f"Created AI video package: {output_path}")
            if attempt > 1:
                print(f"Accepted after {attempt} generation attempts.")
            return
        last_reasons = "; ".join(reasons)
        print(f"Rejected video prompt attempt {attempt}: {last_reasons}")

    raise RuntimeError(f"Could not produce a valid meme video prompt after {MAX_ATTEMPTS} attempts. Last problems: {last_reasons}")


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
        except (OSError, RuntimeError) as exc:
            print(f"Skipped {folder}: {exc}")

    print("Done. No video was published or uploaded automatically.")


if __name__ == "__main__":
    main()
