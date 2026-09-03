# Money Bot

A local-first AI affiliate-content assistant. It generates original short-form content drafts from a product/niche brief, applies safety checks, and stores approved drafts in a local SQLite database.

## Goals

- $0-first local setup using Ollama
- Human approval before anything is published
- No bulk account creation, fake engagement, auto-comments, follow/unfollow, or spam posting
- Conservative content cadence and duplicate detection
- Affiliate disclosure support
- Configurable blocked topics/claims

## Requirements

- Python 3.11+
- Ollama: https://ollama.com/
- A local Ollama model (for example `llama3.2`)

## Windows setup

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

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again.

## Linux/macOS setup

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

## Generate content

Edit `config.json` with your niche and optional affiliate products, then run:

```bash
python money_bot.py generate
```

The bot writes drafts under `content/` and records them in `money_bot.db`.

Review every draft before publishing. The initial version deliberately does **not** auto-post to TikTok, Instagram, X, or other platforms.

## Safety defaults

The generator rejects or flags drafts containing common high-risk patterns, including:

- guaranteed income or guaranteed results
- fake scarcity or fake urgency
- unsupported medical/financial claims
- impersonation
- requests for likes/follows/comments intended to manipulate engagement
- deceptive affiliate disclosures
- repetitive duplicate content

It also adds an affiliate disclosure to promotional drafts when configured.

These safeguards reduce obvious policy risk but cannot guarantee that a platform will accept any particular post. Always check the current rules of the platform and affiliate program before publishing.

## Roadmap

1. Local content generation + safety layer
2. Product/affiliate catalog
3. Template-based video generation with FFmpeg
4. Trend/topic research
5. Analytics and revenue tracking
6. Optional platform publishing integrations with conservative rate limits and manual approval
