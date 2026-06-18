# The Closer — Cold Email Writer + Send Bot

A CLI tool that generates personalized cold emails from outreach targets and sends or drafts them via SMTP. Built for job seekers who want to send thoughtful, human-reviewed outreach emails at a small scale.

## Setup

1. Clone the repo and create a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # macOS / Linux
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your SMTP credentials:

   ```bash
   cp .env.example .env
   ```

## Usage

Run the pipeline (defaults to dry-run mode — no emails sent):

```bash
python -m src.main
```

Review each generated email in the terminal, then choose `send`, `draft`, or `skip`.

Set `DRY_RUN=false` in `.env` to enable real SMTP delivery.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server address |
| `SMTP_PORT` | `587` | SMTP port (STARTTLS) |
| `SMTP_USER` | — | Sender email address |
| `SMTP_PASSWORD` | — | Gmail App Password |
| `SENDER_NAME` | — | Display name on sent emails |
| `DRY_RUN` | `true` | Skip real delivery when true |
| `SEND_MODE` | `draft` | `draft` or `send` |
| `MAX_OUTREACH_PER_RUN` | `5` | Hard cap on contacts per run |
| `INPUT_PATH` | `contacts.json` | Path to outreach targets file |

## Project Structure

```
├── src/
│   ├── main.py            # Orchestrator + CLI loop
│   ├── models.py          # Contact, EmailDraft, LogEntry, DeliveryResult
│   ├── config.py          # Env loading + AppConfig
│   ├── input_loader.py    # JSON/CSV target loading
│   ├── email_generator.py # Template-based email generation
│   ├── preview.py         # Terminal preview + confirmation prompts
│   ├── email_sender.py    # SMTP / dry-run delivery
│   └── logger.py          # outreach_log.csv append
├── docs/
│   ├── architecture.md
│   ├── implementation-plan.md
│   └── problemStatement.md
├── contacts.json          # Sample outreach targets
├── outreach_log.csv       # Audit trail (generated at runtime)
├── .env.example
├── requirements.txt
└── README.md
```

## Safety Features

- **Human review gate** — every email is previewed before any delivery
- **Dry-run mode** — `DRY_RUN=true` by default; no network I/O
- **Volume cap** — `MAX_OUTREACH_PER_RUN` limits contacts per run
- **Personalization required** — emails must include company/role hooks
- **No fabricated content** — template-only generation in MVP
- **Full audit trail** — every attempt logged to `outreach_log.csv`
