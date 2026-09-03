# Money Bot

> A local-first AI content engine for original short-form internet shitposts.

Money Bot uses a local Ollama model to turn a configurable niche and lightweight trend intelligence into short-form content drafts. It includes safety checks, duplicate detection, a review workflow, a terminal CLI, and a small Textual desktop-style interface.

The project is intentionally **local-first and $0-first**. It does not automatically publish content or interact with social platforms.

## What it does

```text
Trend sources ──┐
                ├──> Ollama ──> Draft ──> Safety / Quality ──> Human Review
Niche config ───┘                                      │
                                                       └──> Video prompt
```

### Content generation

- Generates original short-form hooks, premises, scripts, visuals, captions, and CTAs.
- Uses `config.json` for the account identity, audience, tone, and posting limit.
- Uses local Ollama inference by default, so no paid LLM API is required.
- Saves drafts to dated folders under `content/` and tracks them in SQLite.

### Trend intelligence

`trends.py` gathers read-only public signals and feeds them to the content generator as broad inspiration. Trend data is treated as an input, not something to copy.

### Video ideation

`video_prompts.py` turns recent drafts into short, video-native meme concepts. The current direction favors simple visual gags, Wojak-style meme characters, fast cuts, physical punchlines, and 9:16 output for use with an external AI video service.

The repository does **not** automatically generate or upload videos.

## Safety by design

Money Bot deliberately keeps a human in the loop.

It does not:

- auto-post to TikTok, Instagram, X, or other social platforms
- create accounts in bulk
- automate likes, follows, comments, or engagement manipulation
- impersonate people, creators, or companies
- fabricate testimonials, statistics, urgency, scarcity, or social proof
- provide investment advice or token recommendations
- promote affiliate products inside generated videos

The safety layer flags common high-risk patterns, while final publication decisions remain with the user.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/)
- A local Ollama model, such as `llama3.2`
- Git

Python dependencies are listed in `requirements.txt`.

## Quick start — Windows

```powershell
git clone https://github.com/GitMasterFlex99/Money_Bot.git
cd Money_Bot
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
ollama pull llama3.2
python money_bot.py init
```

If PowerShell blocks virtual-environment activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate `.venv` again.

## Quick start — Linux / macOS

```bash
git clone https://github.com/GitMasterFlex99/Money_Bot.git
cd Money_Bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama pull llama3.2
python money_bot.py init
```

## Configure your account

Edit `config.json` before generating content. The checked-in file is a safe example configuration; replace the niche, audience, tone, and other fields with your own project details.

Example:

```json
{
  "niche": "NEET, unemployed, broke, crypto, and terminal internet culture shitposts",
  "audience": "NEETs, unemployed people, broke young adults, crypto traders, and internet-native meme communities",
  "platform": "short-form video",
  "tone": "absurd, dry, chaotic, deadpan, post-ironic, and shitposty",
  "content_goal": "build a funny original account; entertain first and never directly promote affiliate products or tokens",
  "max_posts_per_run": 3
}
```

Do not put API keys, private keys, passwords, or other secrets in `config.json`. Use `.env` for local secrets and keep it uncommitted.

## Generate drafts

```bash
python money_bot.py generate
```

Drafts are saved in:

```text
content/
└── YYYY-MM-DD/
    └── <content-id>/
        ├── hook.txt
        ├── premise.txt
        ├── script.txt
        ├── visuals.txt
        ├── caption.txt
        ├── cta.txt
        └── review.json
```

Every generated draft starts in `review` status. Review it before publishing anywhere.

## Run the GUI

```bash
python money_bot.py gui
```

The interface provides shortcuts for:

- Generate Drafts
- View Latest Drafts
- Run Trend Scan
- View Trend Intelligence
- Run Safety Check
- Open Content Folder

## Trend scan

```bash
python trends.py
```

Trend collection is read-only. It is intended to identify broad themes and behaviors that can inspire original content, not to reproduce source material.

## Generate video concepts

After you have drafts:

```bash
python video_prompts.py --limit 1
```

The tool creates a unique video-prompt file inside the selected draft folder. The output is designed to be pasted into an external AI video generator manually.

Current video direction:

- 6–12 second meme clips
- 1–4 shots
- 9:16 vertical
- Wojak-style meme characters
- simple 2D / 2.5D / low-poly / stylized animation
- physical visual punchlines
- minimal dialogue
- consistent characters, props, rooms, and devices
- no photorealistic or Hollywood-style presentation

## Environment variables

Copy `.env.example` to `.env` and adjust only what you need.

Common settings include:

```text
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
DB_PATH=money_bot.db
CONTENT_DIR=content
```

## Project layout

```text
Money_Bot/
├── money_bot.py       # content generation, safety checks, CLI and GUI
├── trends.py          # read-only trend intelligence collection
├── video_prompts.py   # short-form AI video concept generation
├── config.json        # account/content configuration
├── .env.example       # local environment template
├── requirements.txt   # Python dependencies
└── README.md          # project documentation
```

## Roadmap

- [x] Local Ollama content generation
- [x] Safety and quality checks
- [x] SQLite draft tracking
- [x] Trend intelligence
- [x] Textual GUI
- [x] Video-native prompt generation
- [ ] Optional FFmpeg template rendering
- [ ] Analytics and revenue tracking
- [ ] Optional platform integrations with manual approval and conservative limits

## Disclaimer

This is an experimental content-generation project, not a guaranteed income system. Generated material can contain errors and should be reviewed before publication. Always follow the current rules of the platform and any affiliate program you use.

## License

No license is currently included. Unless a license is added to this repository, the default copyright rules apply to the repository's original code.