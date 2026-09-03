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

    return f"""You create ultra-short animated internet shitpost videos.

THIS IS NOT A SHORT FILM. THIS IS NOT AN AD. THIS IS NOT A STORY.
You are turning the draft into a 6-12 SECOND MEME VIDEO. If the idea cannot fit in 6-12 seconds, simplify it aggressively.

STYLE TARGET
Capture the general energy of short NEET/Chud/wizardposting internet shitposts without copying any particular account, post, artwork, joke, punchline, or distinctive phrase.

The result should feel like:
- a bizarre image that suddenly moves
- one stupid premise taken completely seriously
- blunt internet slang
- deadpan delivery
- awkward/stiff meme animation
- one escalating visual gag
- a hard cut or abrupt final realization

Recurring themes can include NEET life, unemployment, being broke, gaming, terminal internet behavior, Chud/Doomer/Gigachad archetypes, wizardposting/wizardmaxxing, and occasional crypto/memecoin culture. Rotate themes. Do not make every video about crypto or the same character.

WIZARDPOSTING
Wizardposting is encouraged when it naturally fits the premise. Use original absurd fantasy imagery: robes, staffs, candles, improvised spell circles, glowing runes, cursed books, potions, summoning rituals, magical explosions, or ridiculously serious spellcasting over mundane problems. The humor should come from the mismatch between the mundane problem and the absurd magical response.

SLANG
Use internet-native slang naturally when it improves the joke: "maxxing", "mode", "locked in", "bro", "cooked", "it's over", "we are so back", "wizardposting", "wizardmaxxing", and similar language. Do not force slang into every line. Do not reproduce another creator's catchphrases.

VISUAL STYLE
Use stylized meme animation, NOT photorealism:
- 2D, 2.5D, simple 3D, or low-poly animated look
- exaggerated faces and readable silhouettes
- simple ugly/mundane environments
- intentionally awkward or stiff movement
- exaggerated physical reactions
- fast meme timing
- flat or simple lighting
- no Hollywood realism
- no realistic human skin
- no polished commercial aesthetic

DRAFT
HOOK:
{read('hook.txt')}

PREMISE:
{read('premise.txt')}

ORIGINAL SCRIPT:
{read('script.txt')}

EXISTING VISUAL NOTES:
{read('visuals.txt')}

CORE RULES
1. Find ONE central visual joke in the draft.
2. Start on the joke immediately. No intro, setup montage, title card, exposition, or establishing sequence.
3. Target 6-12 seconds total.
4. Use 2-4 shots maximum. One continuous shot is encouraged if funnier.
5. Each shot should usually be 1-4 seconds.
6. Keep dialogue to zero or one very short line unless more is absolutely necessary.
7. The visual action must carry the joke even with sound off.
8. End immediately after the funniest visual beat. Do not explain the joke afterward.
9. Make the final shot the strongest image or reaction.
10. Prefer a mundane situation suddenly becoming absurd rather than a complicated plot.
11. Use 1-2 characters by default, maximum 3.
12. Every character must have a comedic purpose.
13. Do not add random props, locations, devices, characters, or plot points that are not needed for the joke.
14. If a character starts with a desktop PC, keep using that exact PC. Never randomly switch to a laptop or phone.
15. Keep faces, clothing, body type, room layout, lighting, props, and object positions consistent.
16. Never teleport characters or objects between shots.
17. Important captions must be added during editing, not generated inside the AI video. AI-generated text is unreliable.
18. Crypto references are jokes only, never financial advice or token promotion.
19. Do not copy existing memes, jokes, artwork, copyrighted characters, or distinctive creator-specific wording.
20. Do not write generic TikTok/influencer language, motivational content, listicles, product promotion, or educational content.

CHARACTER ARCHETYPES
Choose only what helps the joke:
- original Chud-style Wojak archetype: rough, confident internet guy
- original Doomer-style Wojak archetype: exhausted, bleak internet guy
- original Gigachad-style archetype: absurd confidence
- NPC-style archetype: blank and repetitive
- Soyjak-style archetype: exaggerated reaction
- Bloomer-style archetype: weirdly functional contrast
- unemployed bedroom dweller
- terminally-online gamer
- overconfident crypto bro
- original wizard/wizardposter archetype
- generic normie/wagie for contrast

Do not reproduce any specific artist's exact character design. These are loose archetypes with original visual designs.

CONTINUITY STATE
Before writing, silently lock:
- character appearance
- clothing
- location
- time of day
- lighting
- important props
- exact device
- object positions
- animation style

Do not change these unless the story explicitly requires a transition.

OUTPUT FORMAT
Return ONLY these sections, in this order:

CONCEPT:
One sentence describing the entire visual gag.

CHARACTER BIBLE:
Very concise appearance, clothing, personality, and visual traits.

CONTINUITY LOCK:
Very concise list of location, props, device, clothing, lighting, and object positions.

SHOTS:
SHOT 1 — duration
VISUAL: exactly what is visible and what physically happens.
CAMERA: simple framing/movement.
DIALOGUE/VO: short line or NONE.
SOUND: key sound effect/audio.

SHOT 2 — duration
VISUAL: exactly what is visible and what physically happens.
CAMERA: simple framing/movement.
DIALOGUE/VO: short line or NONE.
SOUND: key sound effect/audio.

Continue only if needed, up to SHOT 4.

MASTER VIDEO PROMPT:
Write one compact prompt for an AI video generator describing the exact characters, setting, visual style, physical action, shot progression, camera, comedic timing, 9:16 framing, continuity, and final punchline. Explicitly require stylized animation and non-photorealistic visuals.

NEGATIVE PROMPT:
Include photorealism, realistic humans, Hollywood cinematic realism, commercial polish, changing faces, changing clothes, extra characters, duplicate characters, disappearing props, device changes, room changes, teleporting objects, unreadable text, malformed hands, extra limbs, watermarks, logos, random cinematic effects, and anything that weakens the meme.

CAPTION TEXT:
Only the short captions to add during editing. Do not depend on AI-generated text.

VOICEOVER:
Optional. Only include if genuinely funny. Keep it extremely short and deadpan.

EDITING NOTES:
Hard cuts, pacing, caption timing, sound effects, pauses, zooms, and the exact punchline moment.

FINAL CHECK BEFORE ANSWERING
- Is it actually 6-12 seconds?
- Is there only ONE central gag?
- Is it visually funny without explanation?
- Is the final beat the strongest beat?
- Is the animation stylized rather than photorealistic?
- Did you avoid copying a specific meme/account?
- Did you preserve continuity?
- Did you avoid unnecessary dialogue and exposition?

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
