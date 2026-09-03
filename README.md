# Money Bot

> Local-first AI content engine for original short-form internet shitposts.

Money Bot combines local Ollama content generation, read-only trend intelligence, safety checks, draft review, and a GPU-free FFmpeg renderer into one small workflow for creating short-form meme videos.

**$0-first. Local-first. Human-reviewed. No automatic posting.**

## What it does

```text
Trend signals ──┐
                ├──> Ollama ──> Draft ──> Safety / Review ──> Video concept
Niche config ───┘                                             │
                                                             v
                                                     FFmpeg meme renderer
                                                             │
                                                             v
                                                        9:16 MP4
                                                             │
                                                             v
                                                     Human review/upload
```

### Content generation

- Generates hooks, premises, scripts, visuals, captions, and CTAs.
- Uses `config.json` for niche, audience, tone, and generation limits.
- Uses local Ollama inference; no paid LLM API is required.
- Stores generated drafts in dated `content/` folders and tracks them in SQLite.
- Includes a Textual desktop-style GUI and terminal CLI.

### Trend intelligence

`trends.py` collects read-only public signals from supported sources and converts them into broad creative inspiration. Source material is not intended to be copied, reposted, or paraphrased into near-duplicates.

### Video concepts

`video_prompts.py` converts drafts into short-form, video-native concepts. The prompt system separates **WOJAK_SHITPOST** content from **DREAMCORE** content so the two visual styles are not mixed accidentally.

### GPU-free video rendering

`meme_renderer.py` assembles local image assets into silent 9:16 MP4 videos using FFmpeg. It supports multiple shots, camera movement, impact shake, grounded transparent character overlays, per-shot character scale/position, and automatic shot concatenation.

The renderer does **not** require a GPU, paid video service, voice model, or generated speech. Add captions and audio during editing when desired.

## Safety by design

Money Bot deliberately keeps a human in the loop.

It does not:

- Auto-post to TikTok, Instagram, X, or other social platforms
- Create accounts in bulk
- Automate likes, follows, comments, or engagement manipulation
- Impersonate people, creators, or companies
- Fabricate testimonials, statistics, urgency, scarcity, or social proof
- Provide investment advice or token recommendations
- Put affiliate-product promotion inside generated videos

Trend intelligence is used for creative direction, not copying source posts or making financial recommendations.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/)
- A local Ollama model such as `llama3.2`
- Git
- FFmpeg (required for video rendering)

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

Verify FFmpeg:

```powershell
ffmpeg -version
```

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
ffmpeg -version
```

## Configure your account

Edit `config.json` to change the account identity and content direction. The repository includes the project's current configuration.

Do not put API keys, private keys, passwords, or other secrets in `config.json`. Use `.env` for local secrets and keep it uncommitted.

## Generate drafts

```bash
python money_bot.py generate
```

Drafts are saved under `content/YYYY-MM-DD/<content-id>/` with hook, premise, script, visuals, caption, CTA, and review files. Every draft starts in review status.

## GUI

```bash
python money_bot.py gui
```

The GUI provides shortcuts for generating drafts, viewing drafts, running trend scans, viewing trend intelligence, running safety checks, and opening the content folder.

## Trend scan

```bash
python trends.py
```

Trend collection is read-only and is intended to identify broad themes and online behavior that can inspire original content.

## Generate video concepts

After generating drafts:

```bash
python video_prompts.py --limit 1
```

The tool creates a video concept/prompt file inside the selected draft folder.

Built-in styles are deliberately separated:

- `WOJAK_SHITPOST` — Wojak-family meme characters, internet culture, visual gags, fast cuts, and absurd escalation.
- `DREAMCORE` — surreal dreamcore environments and the separate wizard character/content style.

## Render a video locally

Renderer test:

```bash
python meme_renderer.py test --output content/renderer_test.mp4
```

Asset-based scene:

```bash
python meme_renderer.py scene scenes/example_uneet_monday.json --output content/dynamic_test.mp4
```

Scene JSON uses one object per shot. Assets are resolved from `assets/backgrounds/` and `assets/characters/` unless a direct path is supplied.

The renderer outputs silent MP4 files. Captions and audio are intentionally separate editing layers.

## Project layout

```text
Money_Bot/
├── money_bot.py              # content generation, safety, CLI and GUI
├── trends.py                 # read-only trend intelligence
├── video_prompts.py          # video-native concept generation
├── meme_renderer.py          # GPU-free FFmpeg video renderer
├── config.json               # account/content configuration
├── .env.example              # local environment template
├── requirements.txt          # Python dependencies
├── assets/                   # characters, backgrounds, props and audio
├── scenes/                   # example renderer scenes
├── .github/workflows/        # automated syntax checks
└── README.md                 # documentation
```

## Status

Money Bot is packaged as a complete local content-generation and meme-rendering toolkit.

Included:

- [x] Local Ollama content generation
- [x] Safety and quality checks
- [x] SQLite draft tracking
- [x] Read-only trend intelligence
- [x] Textual GUI
- [x] Video-native prompt generation
- [x] Separate Wojak and Dreamcore style systems
- [x] GPU-free FFmpeg renderer
- [x] Dynamic camera movement and grounded character compositing
- [x] Example scene
- [x] Automated Python syntax checks

Not included by design:

- Automatic social-media posting
- Paid AI-video API dependency
- GPU-dependent video generation
- Automated engagement
- Guaranteed monetization or income

## Disclaimer

This is an experimental content-generation toolkit, not a guaranteed income system. Generated material can contain errors and should be reviewed before publication. Always follow the current rules of the platform and any affiliate program you use.

## License

MIT License. See `LICENSE`.
