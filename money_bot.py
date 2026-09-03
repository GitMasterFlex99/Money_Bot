from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
DB_PATH = Path(os.getenv("DB_PATH", "money_bot.db"))
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "content"))

BLOCKED_PATTERNS = [
    r"guaranteed?\s+(income|money|profit|returns?|results?)",
    r"guaranteed?\s+to\s+(make|earn)", r"get\s+rich\s+quick", r"risk[- ]free",
    r"100%\s+(guaranteed|safe|effective)", r"cure[sd]?\s+(cancer|depression|anxiety|diabetes)",
    r"doctor[- ]approved", r"financial\s+advice", r"insider\s+tip",
    r"like\s+for\s+like", r"follow\s+for\s+follow", r"comment\s+.{0,20}\s+and\s+win",
    r"pretend\s+to\s+be",
]


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT, content_hash TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL, niche TEXT NOT NULL, product TEXT, status TEXT NOT NULL,
        script TEXT NOT NULL, caption TEXT NOT NULL, flags TEXT NOT NULL)""")
    return conn


def load_config():
    path = Path("config.json")
    if not path.exists(): raise SystemExit("config.json not found")
    return json.loads(path.read_text(encoding="utf-8"))


def safety_scan(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in BLOCKED_PATTERNS if re.search(p, lowered, re.IGNORECASE)]


def quality_scan(text: str) -> list[str]:
    lowered = text.lower(); flags = []
    if lowered.count("also") >= 3: flags.append("quality:multiple_also_jokes")
    if lowered.count("i mean") >= 2: flags.append("quality:overexplaining")
    if lowered.count("and then") >= 4: flags.append("quality:overlong_escalation")
    return flags


def load_trend_analysis() -> str:
    for path in (Path("trend_signals.json"), CONTENT_DIR / "trend_signals.json"):
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return str(data.get("analysis", "") if isinstance(data, dict) else "").strip()
            except (OSError, json.JSONDecodeError):
                return ""
    return ""


def prompt_for(cfg: dict, trend_analysis: str) -> str:
    trend_block = trend_analysis.strip() or "No current trend intelligence is available."
    return f"""You write original short-form shitpost scripts.

ACCOUNT IDENTITY
Niche: {cfg.get('niche', 'NEET, unemployed, broke, crypto, and terminal internet culture shitposts')}
Audience: {cfg.get('audience', 'NEETs, unemployed people, broke young adults, crypto traders, and internet-native meme communities')}
Platform: {cfg.get('platform', 'short-form video')}
Tone: {cfg.get('tone', 'absurd, dry, chaotic, deadpan, post-ironic, and shitposty')}
Goal: {cfg.get('content_goal', 'build a funny original NEET and crypto shitpost account; entertain first and never directly promote affiliate products or tokens')}

CURRENT TREND INTELLIGENCE
{trend_block}

Use trend intelligence only as broad inspiration. Never copy, closely paraphrase,
or reproduce a source joke, post, meme, punchline, wording, or distinctive idea.

CONTENT DIRECTION
The account is primarily about:
- NEET life
- unemployment
- being broke
- job applications and interviews
- living with parents
- gaming and terminal internet habits
- unemployment bureaucracy
- crypto and memecoin culture
- unrealistic internet-money fantasies
- general terminal-online behavior

Crypto is a recurring part of the world, not the subject of every video.
Do not make every video about a specific token.
Do not force the word "NEET" into every script.

CREATIVE RULES
- Create ONE original comedic concept.
- One central premise only.
- Start with a mundane, relatable situation.
- Introduce one specific absurd detail.
- Escalate that same situation.
- End on the strongest deadpan punchline.
- Do not stack unrelated jokes.
- Do not explain the joke.
- Avoid generic TikTok language and forced slang.
- Avoid generic tech content.
- Avoid listicles, explainers, tutorials, news summaries, motivational content, product recommendations, and token explainers.
- Prefer simple situations that can be filmed or shown with basic footage, screen recordings, captions, gaming footage, phone footage, or a talking head.
- The script should sound like something an actual person would say, not an AI essay.
- Keep the spoken script tight enough for roughly 20-45 seconds.

SAFETY AND MONETIZATION RULES
- Never mention affiliate links, referral links, sponsorships, monetization, commissions, or promotional campaigns.
- Never recommend a product or token.
- Never tell viewers to buy, sell, trade, ape, invest, or gamble.
- Never provide financial or investment advice.
- Never fabricate news, statistics, quotes, testimonials, personal experiences, urgency, scarcity, or social proof.
- Never impersonate a real person, creator, company, or source user.
- Never repeat slurs or hateful/derogatory terminology.
- Never request artificial likes, follows, comments, shares, views, or engagement.

OUTPUT FORMAT
Return ONLY the six sections below. Do not add an introduction, explanation, markdown fence, or extra headings.
Use the headings exactly as written. Put the content on the next line.

HOOK:
One short attention-grabbing opening sentence.

PREMISE:
One or two sentences describing the single comedic setup.

SCRIPT:
The complete spoken script. The hook may be used as the opening line, but the script must still be complete.

VISUALS:
Simple visual suggestions.

CAPTION:
A short natural caption.

CTA:
NONE

All six headings are mandatory. CTA must be exactly NONE."""


def ollama_generate(prompt: str) -> str:
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=180)
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.RequestException as exc:
        raise SystemExit(f"Could not reach Ollama at {OLLAMA_URL}: {exc}") from exc


def parse_package(text: str) -> tuple[str, str, str, str, str, str]:
    """Parse headings even when Ollama adds markdown, bullets, numbering, or inline values."""
    sections: dict[str, list[str]] = {}
    current = None
    names = ("HOOK", "PREMISE", "SCRIPT", "VISUALS", "CAPTION", "CTA")
    heading_re = re.compile(r"^(?:[#>*`\-\s]*)(HOOK|PREMISE|SCRIPT|VISUALS|CAPTION|CTA)\s*:?\s*(.*)$", re.IGNORECASE)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        clean = re.sub(r"^[`*#>\-\s]+|[`*#\s]+$", "", line).strip()
        match = heading_re.match(line) or heading_re.match(clean)
        if match and match.group(1).upper() in names:
            current = match.group(1).upper()
            sections.setdefault(current, [])
            inline = match.group(2).strip().strip("`*_")
            if inline and inline.lower() not in {"one short attention-grabbing opening sentence.", "one or two sentences describing the single comedic setup.", "the complete spoken script.", "simple visual suggestions.", "a short natural caption.", "none"}:
                sections[current].append(inline)
            elif current == "CTA":
                sections[current].append("NONE")
            continue
        if current:
            sections[current].append(raw_line)

    def get_section(name: str, default: str = "") -> str:
        value = "\n".join(sections.get(name, [])).strip()
        value = re.sub(r"^(?:```\w*\s*)|(?:\s*```)$", "", value, flags=re.IGNORECASE).strip()
        return value or default

    hook = get_section("HOOK")
    premise = get_section("PREMISE")
    script = get_section("SCRIPT")
    visuals = get_section("VISUALS", "Simple footage matching the script: bedroom, phone, computer screen, gaming footage, charts, job-search screen, or talking head.")
    caption = get_section("CAPTION", "another completely normal day")
    cta = get_section("CTA", "NONE")
    missing = [n for n, v in (("HOOK", hook), ("PREMISE", premise), ("SCRIPT", script)) if not v]
    if missing: raise ValueError(f"Model response missing sections: {', '.join(missing)}")
    return hook, premise, script, visuals, caption, cta


def save_content(cfg: dict, hook: str, premise: str, script: str, visuals: str, caption: str, cta: str, flags: list[str]):
    payload = "\n".join([hook, premise, script, visuals, caption, cta])
    content_hash = hashlib.sha256(payload.lower().encode("utf-8")).hexdigest()
    conn = db()
    if conn.execute("SELECT id FROM content WHERE content_hash = ?", (content_hash,)).fetchone():
        conn.close(); return None, "duplicate"
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("INSERT INTO content(content_hash, created_at, niche, product, status, script, caption, flags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 (content_hash, now, cfg.get("niche", ""), None, "review", script, caption, json.dumps(flags)))
    conn.commit(); conn.close()
    folder = CONTENT_DIR / datetime.now().strftime("%Y-%m-%d") / content_hash[:8]
    folder.mkdir(parents=True, exist_ok=True)
    for name, value in (("hook", hook), ("premise", premise), ("script", script), ("visuals", visuals), ("caption", caption), ("cta", cta)):
        (folder / f"{name}.txt").write_text(value, encoding="utf-8")
    (folder / "review.json").write_text(json.dumps({"status": "review", "flags": flags}, indent=2), encoding="utf-8")
    return folder, "created"


def generate() -> None:
    cfg = load_config(); limit = max(1, min(int(cfg.get("max_posts_per_run", 3)), 5)); trend_analysis = load_trend_analysis(); created = 0
    for _ in range(limit):
        raw = ollama_generate(prompt_for(cfg, trend_analysis))
        try:
            hook, premise, script, visuals, caption, cta = parse_package(raw)
        except ValueError as exc:
            print(f"Skipped malformed model output: {exc}")
            continue
        combined = "\n".join([hook, premise, script, visuals, caption, cta])
        flags = safety_scan(combined) + quality_scan(combined)
        folder, result = save_content(cfg, hook, premise, script, visuals, caption, cta, flags)
        if result == "duplicate": print("Skipped duplicate draft."); continue
        created += 1; print(f"Created review draft: {folder}")
        if flags: print("  FLAGS: manual review required")
    print(f"Done. Created {created} draft(s). Nothing was published automatically.")


def init() -> None:
    db().close(); CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Initialized database: {DB_PATH}"); print(f"Content directory: {CONTENT_DIR}")


def launch_gui() -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Container, VerticalScroll
        from textual.widgets import Button, Footer, Header, RichLog, Static
    except ImportError as exc:
        print(f"GUI dependency import failed: {exc}"); return
    class MoneyBotApp(App):
        TITLE = "Money Bot"; SUB_TITLE = "NEET / Crypto Shitpost Engine"
        CSS = """
        Screen { align: center middle; }
        #main { width: 92%; height: 92%; border: round $accent; padding: 1 2; }
        #title { height: auto; padding: 1; text-align: center; }
        #menu { height: auto; padding: 1 0; }
        Button { width: 100%; margin: 0 0 1 0; }
        #output { height: 1fr; border: round $accent; padding: 1; }
        """
        def compose(self) -> ComposeResult:
            yield Header()
            with Container(id="main"):
                yield Static("NEET / CRYPTO SHITPOST ENGINE\nGenerate, review and manage drafts", id="title")
                with VerticalScroll(id="menu"):
                    yield Button("Generate Drafts", id="generate"); yield Button("View Latest Drafts", id="drafts")
                    yield Button("Run Trend Scan", id="trends"); yield Button("View Trend Intelligence", id="trend_view")
                    yield Button("Run Safety Check", id="safety"); yield Button("Open Content Folder", id="open_content"); yield Button("Exit", id="exit")
                yield RichLog(id="output", markup=True, wrap=True)
            yield Footer()
        def write_output(self, message: str) -> None: self.query_one("#output", RichLog).write(message)
        def on_mount(self) -> None: self.write_output("[bold]Ready.[/bold]"); self.write_output("Choose an action from the menu.")
        def on_button_pressed(self, event: Button.Pressed) -> None:
            action = event.button.id
            if action == "generate": self.run_generate()
            elif action == "drafts": self.show_drafts()
            elif action == "trends": self.run_trends()
            elif action == "trend_view": self.show_trends()
            elif action == "safety": self.run_safety()
            elif action == "open_content": self.open_content()
            elif action == "exit": self.exit()
        def run_generate(self) -> None:
            self.write_output("[bold]Generating drafts...[/bold]")
            result = subprocess.run([sys.executable, __file__, "generate"], cwd=Path(__file__).resolve().parent, capture_output=True, text=True)
            if result.stdout.strip(): self.write_output(result.stdout.strip())
            if result.stderr.strip(): self.write_output(f"[red]{result.stderr.strip()}[/red]")
            self.write_output("[green]Generation complete.[/green]" if result.returncode == 0 else f"[red]Generation failed (exit {result.returncode}).[/red]")
        def show_drafts(self) -> None:
            root = Path(__file__).resolve().parent; content_dir = root / CONTENT_DIR
            if not content_dir.exists(): self.write_output("No content folder exists yet."); return
            files = sorted(content_dir.rglob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not files: self.write_output("No drafts found."); return
            self.write_output("[bold]Latest draft files:[/bold]")
            for path in files[:30]: self.write_output(f"\n[bold]{path.parent.name}/{path.name}[/bold]"); self.write_output(path.read_text(encoding="utf-8")[:4000])
        def run_trends(self) -> None:
            root = Path(__file__).resolve().parent; trends_file = root / "trends.py"
            if not trends_file.exists(): self.write_output("[red]trends.py not found.[/red]"); return
            self.write_output("[bold]Running trend scan...[/bold]")
            result = subprocess.run([sys.executable, str(trends_file)], cwd=root, capture_output=True, text=True)
            if result.stdout.strip(): self.write_output(result.stdout.strip())
            if result.stderr.strip(): self.write_output(f"[red]{result.stderr.strip()}[/red]")
        def show_trends(self) -> None:
            analysis = load_trend_analysis(); self.write_output("[bold]Trend Intelligence[/bold]\n" + (analysis or "No trend intelligence available."))
        def run_safety(self) -> None:
            self.write_output("[bold]Running safety check...[/bold]"); root = Path(__file__).resolve().parent
            files = sorted(root.joinpath(CONTENT_DIR).rglob("script.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not files: self.write_output("No scripts found."); return
            for path in files[:20]:
                flags = safety_scan(path.read_text(encoding="utf-8")) + quality_scan(path.read_text(encoding="utf-8"))
                self.write_output(f"{path.parent.name}: " + ("FLAGS: " + ", ".join(flags) if flags else "PASS"))
        def open_content(self) -> None:
            root = Path(__file__).resolve().parent; content_dir = root / CONTENT_DIR; content_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(content_dir)); self.write_output(f"Opened: {content_dir}")
    MoneyBotApp().run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Money Bot"); parser.add_argument("command", choices=["init", "generate", "gui"]); args = parser.parse_args()
    if args.command == "init": init()
    elif args.command == "generate": generate()
    elif args.command == "gui": launch_gui()


if __name__ == "__main__": main()
