# Implementation Plan: The Closer

Phase breakdown based on [architecture.md](./architecture.md) and [problemStatement.md](./problemStatement.md). Uses the vertical-slice demo order from the architecture doc.

---

## Phase 0 — Project Scaffolding

**Goal:** Empty project structure, one `python main.py` entry point, no logic.

| Step | Action | Files |
|------|--------|-------|
| 0.1 | Create root directory and `docs/` | — |
| 0.2 | Write `.gitignore` (`.env`, `*.pyc`, `__pycache__`, `.DS_Store`) | `.gitignore` |
| 0.3 | Write `requirements.txt` (`python-dotenv` only) | `requirements.txt` |
| 0.4 | Write `.env.example` with all vars from architecture §5.7 | `.env.example` |
| 0.5 | Create empty `main.py` with `if __name__ == "__main__": print("Hello from The Closer")` | `main.py` |

**Verification:** `python main.py` prints the greeting.

---

## Phase 1 — Domain Model + Config

**Goal:** Data classes and config loading wired, no pipeline logic yet.

| Step | Action | Files |
|------|--------|-------|
| 1.1 | Write `models.py` with `Contact`, `EmailDraft`, `LogEntry`, `DeliveryResult` dataclasses | `models.py` |
| 1.2 | Write `config.py` with `AppConfig` dataclass + `load_config()` from `.env` | `config.py` |

**Key decisions:**
- `Contact`: all fields from problem statement §5; 5 required, 6 optional
- `EmailDraft`: `subject`, `body`, `word_count`
- `LogEntry`: `timestamp`, `recipient_email`, `company`, `role`, `subject`, `status`, `error_message`
- `DeliveryResult`: `status`, `provider_message_id`, `error`
- `AppConfig`: all vars from architecture §5.7 table
- `load_config()` uses `python-dotenv`; defaults for everything except SMTP creds

**Verification:** `python -c "from config import load_config; print(load_config())"` prints config with defaults.

---

## Phase 2 — Input Loader (FR1)

**Goal:** Load outreach targets from a data source.

| Step | Action | Files |
|------|--------|-------|
| 2.1 | Write `src/input_loader.py` with `load_targets()` | `src/input_loader.py` |
| 2.2 | Write `contacts.json` with 5 sample records (realistic company/role combos) | `contacts.json` |

**Key decisions:**
- Start with JSON loader (`contacts.json`), skip CSV for MVP
- `load_targets(path)` → `list[Contact]`
- Validate required fields per architecture §5.2 table; skip invalid records with warning
- Default `recipient_name` to `"there"` if missing
- 5 sample contacts in `contacts.json` to meet acceptance criteria (≥5 emails)

**Verification:** `python -c "from input_loader import load_targets; print(load_targets('contacts.json'))"` prints 5 Contact objects.

---

## Phase 3 — Email Generator (FR2)

**Goal:** Generate subject + body following the 6-part email anatomy, <150 words.

| Step | Action | Files |
|------|--------|-------|
| 3.1 | Write `email_generator.py` with `generate_email()` | `email_generator.py` |

**Key decisions:**
- Deterministic Python f-string template (no LLM in MVP)
- Template maps to the 6 sections from problem statement §7
- Post-generation word count check; warn if >150
- If `personalization_note` is missing, derive hook from `company` + `role`
- No invented facts — only interpolate provided fields

**Verification:** `python -c "from models import Contact; from email_generator import generate_email; c = Contact(...); d = generate_email(c, config); print(d.subject); print(d.body); print(d.word_count)"` — word count ≤ 150.

---

## Phase 4 — Preview + Confirmation (FR3)

**Goal:** Human-in-the-loop gate before delivery.

| Step | Action | Files |
|------|--------|-------|
| 4.1 | Write `preview.py` with `preview_email()` and `prompt_action()` | `preview.py` |

**Key decisions:**
- `preview_email(draft, contact)` pretty-prints: company, role, recipient, subject, body, word count
- `prompt_action()` → `"send"` | `"draft"` | `"skip"`
- Terminal prompt with clear formatting (separator lines, field labels)
- No network I/O in this phase

**Verification:** Pipe through a contact and draft; confirm terminal output looks right and prompt accepts valid input.

---

## Phase 5 — Email Sender (FR4)

**Goal:** Deliver email via SMTP or dry-run.

| Step | Action | Files |
|------|--------|-------|
| 5.1 | Write `email_sender.py` with `deliver_email()` + `DryRunEmailSender` | `email_sender.py` |

**Key decisions:**
- Start with `DryRunEmailSender` (returns success, no network)
- Next: SMTP via `smtplib` with STARTTLS (port 587)
- `deliver_email()` selects sender based on `DRY_RUN` flag
- `DeliveryResult` returned for every call
- Clear error messages for SMTP auth failures (hint about Gmail App Passwords)

**Verification (dry run):** `python -c "from email_sender import deliver_email; ... result = deliver_email(...); print(result)"` returns status without network.

**Verification (SMTP):** Set `DRY_RUN=false` and send one email to your own address.

---

## Phase 6 — Logger (FR5)

**Goal:** Append-only CSV audit trail.

| Step | Action | Files |
|------|--------|-------|
| 6.1 | Write `logger.py` with `append_log()` | `logger.py` |

**Key decisions:**
- Append-only via `csv.writer`; create file with headers if missing
- Columns from architecture §5.6: `timestamp`, `recipient_email`, `company`, `role`, `subject`, `status`, `error_message`, `word_count`, `job_url`
- Lock-free (single-process CLI is fine)
- Accept `LogEntry` dataclass and optional file path

**Verification:** `python -c "from logger import append_log; from models import LogEntry; append_log(LogEntry(...))"` creates `outreach_log.csv` with header and one row.

---

## Phase 7 — Orchestrator (main.py)

**Goal:** Wire the full pipeline: load → generate → preview → confirm → send → log.

| Step | Action | Files |
|------|--------|-------|
| 7.1 | Rewrite `main.py` with `run_outreach_pipeline()` and batch summary | `main.py` |

**Key decisions:**
- Architecture §5.1 pseudocode translated directly to Python
- Per-contact state machine: Loaded → Generated → Previewed → (skip/deliver) → Done
- Hard cap at `MAX_OUTREACH_PER_RUN` (default 5)
- Batch summary printed at end (sent / drafted / skipped / failed counts)
- `DRY_RUN=true` skips real delivery, logs as `generated`

**Verification:** `python main.py` with `DRY_RUN=true` runs full pipeline on all 5 contacts, shows preview + prompts, logs each outcome.

---

## Phase 8 — Live Demo Run

**Goal:** One real email sent to your own address, proof collected.

| Step | Action |
|------|--------|
| 8.1 | Set `DRY_RUN=false` and `SMTP_*` vars in `.env` with Gmail App Password |
| 8.2 | Update one contact's `recipient_email` to your own address |
| 8.3 | Run `python main.py`, confirm preview, type `send` |
| 8.4 | Verify email arrives in inbox |
| 8.5 | Take screenshot of Sent folder + `outreach_log.csv` for proof |

---

## Stretch Phases (Post-MVP)

| Phase | Feature | Files changed |
|-------|---------|---------------|
| S1 | Gmail API draft mode (OAuth) | `email_sender.py` — add `GmailApiEmailSender` |
| S2 | CSV input loader | `input_loader.py` — add CSV parser |
| S3 | Streamlit UI | New `ui/` directory, calls same pipeline functions |
| S4 | LLM email rewriting (Groq) | `email_generator.py` — add `LLMEmailGenerator` with Groq |
| S5 | Email quality / spam scoring | New `validator.py` — post-processor before preview |
| S6 | Follow-up generator | New `followup_generator.py` + log linking |
| S7 | Deduplication + opt-out store | `input_loader.py` — filter against past log |
| S8 | Multiple subject suggestions | Generator returns `list[str]`, user picks in preview |

---

## File Creation Order Summary

```
 1.  .gitignore
 2.  requirements.txt
 3.  .env.example
 4.  models.py
 5.  config.py
 6.  input_loader.py
 7.  contacts.json
 8.  email_generator.py
 9.  preview.py
10.  email_sender.py
11.  logger.py
12.  main.py          (rewrite scaffold from Phase 0)
```

---

## Acceptance Criteria Checklist

| Criterion | Phase | How verified |
|-----------|-------|-------------|
| ≥5 personalized emails | 2 + 3 | 5 contacts in JSON + generator produces unique body per record |
| Subject + body | 3 | `EmailDraft.subject` + `EmailDraft.body` non-empty |
| Company/role personalization | 3 | Template interpolates `company` and `role` |
| Preview before send | 4 | `preview_email()` called before any delivery |
| Send or draft successfully | 5 + 8 | SMTP delivery or dry-run returns success |
| Log each attempt | 6 | Row appended for every contact |
| Proof via Sent/Drafts | 8 | Screenshot + `outreach_log.csv` status column |
fts | 8 | Screenshot + `outreach_log.csv` status column |
