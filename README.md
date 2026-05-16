# medium-scrapper (MCP)

This repo exposes the Medium tag scraper as a local MCP server for Claude Desktop (Windows).

## What you get

- A local MCP server Claude Desktop can launch automatically.
- Tools that let Claude fetch Medium RSS items for a tag (dynamic) and extract readable text.
- Optional CSV export.

## Prerequisites

- Windows 10/11
- Python 3.10+ (you have Python 3.13 which is fine)
- Internet access (to reach `medium.com`)
- Claude Desktop installed

## Installation (recommended: virtual environment)

Run these commands in PowerShell:

```powershell
cd C:\Users\DELL\OneDrive\Desktop\medium-scrapper

# Create a virtual environment (isolated Python install for this server)
python -m venv .venv

# Install dependencies into the venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Why a venv? Claude Desktop may launch a different `python` than the one you use in your terminal. Pointing Claude Desktop at `.\.venv\Scripts\python.exe` guarantees the `mcp` package and dependencies are available.

## One-click install (PowerShell)

If you want a single script that installs everything into a clean folder (but leaves Claude config changes to you), run from a local checkout:

```powershell
cd C:\Users\DELL\OneDrive\Desktop\medium-scrapper
.\install.ps1 -InstallDir "$HOME\medium-scraper-mcp"
```

Then use the printed `command` + `args` values in your Claude Desktop config.

### One-click install from GitHub (clone)

If you want the installer to clone the repo for you (requires Git installed):

```powershell
.\install.ps1 -InstallDir "$HOME\medium-scraper-mcp" -RepoUrl "https://github.com/TahaKhan192004/medium-scrapper.git"
```

## Configure Claude Desktop

Edit your Claude Desktop MCP config and add this server entry (keep your other servers as-is):

```json
{
  "mcpServers": {
    "medium-scraper": {
      "command": "C:/Users/DELL/OneDrive/Desktop/medium-scrapper/.venv/Scripts/python.exe",
      "args": ["C:/Users/DELL/OneDrive/Desktop/medium-scrapper/mcp_server.py"]
    }
  }
}
```

Then fully quit Claude Desktop and open it again.

## Quick verification (optional)

You can run the server manually to confirm it starts (Claude Desktop does this automatically later):

```powershell
cd C:\Users\DELL\OneDrive\Desktop\medium-scrapper
.\.venv\Scripts\python.exe mcp_server.py
```

If it starts successfully, it will wait for MCP connections. Stop with `Ctrl+C`.

## Claude Desktop setup

If you prefer using the MCP CLI (instead of manually editing Claude config), you can try:

```powershell
.\.venv\Scripts\python.exe -m mcp install mcp_server.py --name "Medium Scraper"
```

Note: the manual config method is the most transparent and easiest to debug on Windows.

## Tools

- `fetch_medium_tag_articles(tag, limit=10)`
  - **tag**: the last part of the RSS URL. Example: for `https://medium.com/feed/tag/claude`, `tag="claude"`.
  - **limit**: requested items to attempt from the feed. Capped to `50`.
  - Returns: list of `{title, url, content}`.

- `fetch_medium_tag_articles_to_csv(tag, limit=10, csv_path="medium_articles.csv")`
  - Same as above, but also writes a CSV to `csv_path`.
  - Returns: `{csv_path, scraped, requested}`.

## How to use it in Claude

Once Claude Desktop has started the server successfully, you can ask Claude things like:

- “Use the Medium Scraper tool to fetch 5 articles for the tag `claude` and summarize them.”
- “Fetch 10 articles for the tag `ai` and save them to `ai_articles.csv`.”
- “Fetch 20 articles for `machine-learning`, then extract the key takeaways.”

## Notes / troubleshooting

- If Claude logs `ModuleNotFoundError: No module named 'mcp'`, your config is pointing to the wrong Python. Fix it by setting `command` to the venv python:
  - `C:/Users/DELL/OneDrive/Desktop/medium-scrapper/.venv/Scripts/python.exe`
- If dependency install fails with network / firewall errors, make sure Python/pip is allowed to access the internet (or install from your company-approved package mirror).
- If scraping fails intermittently, Medium may serve anti-bot pages. The scraper retries and may return fewer items than requested.
