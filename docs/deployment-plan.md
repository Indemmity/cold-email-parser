# Deployment Plan — The Closer

## Overview

This project is a Python cold-email writer with a Streamlit web UI. It has **3 dependencies** (`python-dotenv`, `streamlit`, `pandas`) and no database. This document covers two deployment paths:

- **Streamlit Cloud** — free, zero infra, git-based deploys (recommended)
- **Docker self-hosting** — full control, persistent log file

---

## Option 1: Streamlit Cloud (Recommended)

### Prerequisites

- A GitHub account
- The repository pushed to GitHub (public or private)

### What's already done

The following changes are already in the codebase so you can skip straight to deploying:

- `app.py` — root entry point that Streamlit Cloud can discover
- `src/config.py` — reads from Streamlit Secrets first, falls back to `.env` for local dev

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository, branch (`main`), and set **Main file** to `app.py`
5. Click **"Deploy"**

The app will build and deploy in about 2–3 minutes. You'll get a URL like `https://<app-name>.streamlit.app`.

### Step 3 — Configure secrets

After deployment, the app needs your SMTP credentials to send emails. Since `.env` isn't uploaded to git, you need to add secrets via the Streamlit Cloud dashboard.

1. In your deployed app dashboard, go to **"Settings"** → **"Secrets"**
2. Add each variable as a separate line:

```toml
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "your-16-char-app-password"
SENDER_NAME = "Your Name"
DRY_RUN = "true"
SEND_MODE = "draft"
MAX_OUTREACH_PER_RUN = "5"
```

3. Click **"Save"** → the app will auto-restart

**Important:** Keep `DRY_RUN = "true"` on first deploy. Change to `"false"` only when you're ready to send real emails.

### Step 4 — Use the app

1. Open your deployed URL
2. In the sidebar, upload a `contacts.json` file (use the "Uploaded" button)
3. Go to the **Pipeline** tab to review and process each contact

**Note on the log:** `outreach_log.csv` is ephemeral on Streamlit Cloud — it resets whenever the app restarts (due to idling or redeploy). This is fine for demo/trial use. Download the log CSV from the **Log** tab before it resets.

### Updating after deployment

Every time you push to your GitHub repo, Streamlit Cloud auto-deploys:

```bash
git add .
git commit -m "Some change"
git push
```

---

## Option 2: Docker Self-Hosting

Use this when you need persistent log storage or want to run on a VPS.

### Step 1 — Create these files

**`Dockerfile`** (in project root):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**`.dockerignore`** (in project root):

```
.env
.venv/
__pycache__/
*.pyc
.git/
.commandcode/
outreach_log.csv
```

### Step 2 — Build and run

```bash
# Build the image
docker build -t the-closer .

# Run with .env for credentials, persistent log volume
docker run -d \
  --name closer \
  -p 8501:8501 \
  --env-file .env \
  -v ./outreach_log.csv:/app/outreach_log.csv \
  the-closer
```

Or use Docker Compose — create **`docker-compose.yml`**:

```yaml
version: "3.9"

services:
  closer:
    build: .
    ports:
      - "8501:8501"
    env_file: .env
    volumes:
      - ./outreach_log.csv:/app/outreach_log.csv
```

Then:

```bash
docker compose up -d
```

Open `http://localhost:8501` in a browser.

### Step 3 — Set up `.env`

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual SMTP credentials.

---

## Option 3: Render / Hugging Face Spaces

Both support one-click Streamlit deploys. Same process as Streamlit Cloud — connect your repo, set the entry point to `app.py`, and configure secrets in their dashboard instead of `.env`.

- **Render:** Offers a persistent disk add-on if you want the CSV log to survive restarts
- **Hugging Face Spaces:** Free, ephemeral storage (same limitation as Streamlit Cloud)

---

## Environment Variables Reference

| Variable | Default | Required | Notes |
|---|---|---|---|
| `SMTP_HOST` | `smtp.gmail.com` | No | SMTP server address |
| `SMTP_PORT` | `587` | No | SMTP port (STARTTLS) |
| `SMTP_USER` | — | **Yes** | Gmail/email address |
| `SMTP_PASSWORD` | — | **Yes** | Gmail App Password (16 chars) |
| `SENDER_NAME` | — | **Yes** | Display name on sent emails |
| `DRY_RUN` | `true` | No | `false` to send real emails |
| `SEND_MODE` | `draft` | No | `draft` or `send` |
| `MAX_OUTREACH_PER_RUN` | `5` | No | Caps contacts processed per session |
| `INPUT_PATH` | `contacts.json` | No | Only used in CLI mode |
| `LOG_PATH` | `outreach_log.csv` | No | Only used in CLI mode |
| `GROQ_API_KEY` | — | No | For LLM rewriting (future) |
| `LLM_PROVIDER` | `groq` | No | LLM provider (future) |
| `LLM_MODEL` | `mixtral-8x7b-32768` | No | LLM model (future) |

---

## Gotchas

- **App password, not your Gmail password** — enable 2FA on your Google account and generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- **Log resets on Streamlit Cloud** — the filesystem is ephemeral. Download your log from the **Log** tab before the app idles or restarts
- **No database** — the app is flat-file only. All state is in `outreach_log.csv` and your browser's session state
- **contacts.json must be uploaded** — on Streamlit Cloud, use the file uploader in the sidebar. The built-in "Default" button reads from disk and won't work on cloud deployments (the contacts.json is bundled in the image but the path may differ)
