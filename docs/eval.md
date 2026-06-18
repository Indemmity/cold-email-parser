# Evaluation: The Closer

Phase-by-phase evaluation criteria for AI-generated code. Each phase lists what to check, how to test it, and pass/fail thresholds.

---

## How to Use This Document

For each phase, run through the checklist **in order**. If any **must-pass** check fails, the phase is not ready — flag it, fix it, and re-run before moving to the next phase. **Should-pass** checks are warnings: note them but don't block the phase.

All phases assume the repo is at `the-closer/` and commands run from that directory.

---

## Phase 0 — Project Scaffolding

### Acceptance criteria

- Project directory exists with correct structure
- `python main.py` prints without error
- `.gitignore` excludes `.env`, `*.pyc`, `__pycache__`, `.DS_Store`
- `.env.example` lists all expected vars

### Test procedure

```
cd the-closer/
python main.py
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 0.1 | `main.py` exists and runs | must-pass | `python main.py` | Prints some output (any string), exits with code 0 |
| 0.2 | `.gitignore` exists | must-pass | `dir .gitignore 2>nul || echo MISSING` on Windows | File exists |
| 0.3 | `.env` is gitignored | should-pass | `git check-ignore .env` | Returns `.env` (only works if git is initialized) |
| 0.4 | `.env.example` exists | must-pass | `dir .env.example` | File exists |
| 0.5 | `.env.example` has `DRY_RUN=true` | must-pass | `findstr DRY_RUN .env.example` | Line present |
| 0.6 | `.env.example` has `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SENDER_NAME`, `SEND_MODE`, `MAX_OUTREACH_PER_RUN` | should-pass | Check file | All vars present |
| 0.7 | `requirements.txt` exists | must-pass | `dir requirements.txt` | File exists |
| 0.8 | `requirements.txt` has `python-dotenv` | should-pass | `findstr python-dotenv requirements.txt` | Line present |

---

## Phase 1 — Domain Model + Config

### Acceptance criteria

- `models.py` defines `Contact`, `EmailDraft`, `LogEntry`, `DeliveryResult` dataclasses
- `config.py` defines `AppConfig` dataclass and `load_config()` function
- `load_config()` reads from `.env` and applies defaults

### Test procedure

```
# Test domain model imports
python -c "from models import Contact, EmailDraft, LogEntry, DeliveryResult; print('Models OK')"

# Test config loading with default values
python -c "from config import load_config; c = load_config(); print(c)"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 1.1 | `models.py` imports cleanly | must-pass | `python -c "from models import Contact, EmailDraft, LogEntry, DeliveryResult"` | No ImportError |
| 1.2 | `Contact` has all 5 required fields | must-pass | `c = Contact(recipient_email='a@b.com', company='C', role='R', candidate_name='N', candidate_background='B')` in interpreter | No TypeError |
| 1.3 | `Contact` optional fields default correctly | must-pass | `c = Contact(recipient_email='a@b.com', company='C', role='R', candidate_name='N', candidate_background='B')`; check `c.recipient_name is None` | None default works |
| 1.4 | `EmailDraft` has `subject`, `body`, `word_count` | must-pass | `d = EmailDraft(subject='S', body='B', word_count=10)` | Instantiates without error |
| 1.5 | `LogEntry` has `timestamp`, `recipient_email`, `company`, `role`, `subject`, `status`, `error_message` | must-pass | `LogEntry(timestamp='...', recipient_email='...', company='...', role='...', subject='...', status='...')` | Instantiates without error |
| 1.6 | `LogEntry.error_message` defaults to empty string | must-pass | `LogEntry(timestamp='...', recipient_email='...', company='...', role='...', subject='...', status='...').error_message` | Equals `""` |
| 1.7 | `DeliveryResult` has `status`, `provider_message_id`, `error` | must-pass | `DeliveryResult(status='sent', provider_message_id=None, error=None)` | Instantiates without error |
| 1.8 | `config.py` loads without `.env` present | must-pass | Rename `.env` to `.env.bak`, run `python -c "from config import load_config; load_config()"` | No crash; uses defaults |
| 1.9 | `load_config()` returns expected default values | must-pass | `c = load_config(); print(c.DRY_RUN, c.MAX_OUTREACH_PER_RUN, c.SEND_MODE)` | `DRY_RUN=True`, `MAX_OUTREACH_PER_RUN=5`, `SEND_MODE="draft"` |
| 1.10 | `load_config()` reads from `.env` when present | must-pass | Create `.env` with `DRY_RUN=false`; `c = load_config(); print(c.DRY_RUN)` | `False` (not `True`) |
| 1.11 | `SMTP_PORT` defaults to 587 | should-pass | `c = load_config(); print(c.SMTP_PORT)` | `587` |
| 1.12 | `MAX_OUTREACH_PER_RUN` is `int` type | must-pass | `c = load_config(); print(type(c.MAX_OUTREACH_PER_RUN))` | `<class 'int'>` |

**Restore `.env` after testing.**

---

## Phase 2 — Input Loader (FR1)

### Acceptance criteria

- `input_loader.py` exports `load_targets()`
- `load_targets(path)` returns `list[Contact]`
- Validates required fields; skips invalid records with warning
- `contacts.json` has 5 realistic sample records

### Test procedure

```
python -c "from input_loader import load_targets; contacts = load_targets('contacts.json'); print(f'Loaded {len(contacts)} contacts'); [print(c.recipient_email, c.company, c.role) for c in contacts]"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 2.1 | `load_targets()` returns `list[Contact]` | must-pass | Run test procedure; check first element type | Each element is `Contact` |
| 2.2 | 5 contacts loaded | must-pass | Test procedure output | Exactly 5 contacts |
| 2.3 | All contacts have distinct recipient/company/role combos | should-pass | Visual inspect output or compare field sets | No two identical records |
| 2.4 | Each contact has all 5 required fields populated | must-pass | `all(c.recipient_email and c.company and c.role and c.candidate_name and c.candidate_background for c in contacts)` | `True` |
| 2.5 | Missing `contacts.json` raises `FileNotFoundError` | must-pass | `load_targets('nonexistent.json')` | Raises `FileNotFoundError` |
| 2.6 | Malformed JSON raises clear error | must-pass | Create `bad.json` with `{bad`; `load_targets('bad.json')` | Raises `json.JSONDecodeError` or clear wrapper |
| 2.7 | Empty list returns `[]` | must-pass | Create `empty.json` with `[]`; `len(load_targets('empty.json'))` | `0` |
| 2.8 | Record missing `recipient_email` is skipped | must-pass | Create test file with 1 valid + 1 missing email; result length is 1 | Only valid record returned |
| 2.9 | Record missing `company` is skipped | must-pass | Same as 2.8 but missing company | Only valid record returned |
| 2.10 | Record with invalid email format is skipped | must-pass | Add record with `recipient_email: "not-email"` | Record not in output |
| 2.11 | `recipient_name` defaults to `"there"` | must-pass | Record without `recipient_name`; check `.recipient_name` | `"there"` |
| 2.12 | Input fields with extra whitespace are stripped | must-pass | Record with `"  Acme  "` as company; check `.company` | `"Acme"` |
| 2.13 | `contacts.json` has realistic sample data | should-pass | Open and read file | Companies exist, roles are real-sounding job titles |

---

## Phase 3 — Email Generator (FR2)

### Acceptance criteria

- `email_generator.py` exports `generate_email(contact, config)` → `EmailDraft`
- Subject is short and role-specific
- Body follows 6-part cold email anatomy
- Word count ≤ 150

### Test procedure

```
python -c "
from models import Contact
from config import load_config
from email_generator import generate_email

config = load_config()
c = Contact(
    recipient_email='priya@acme.com',
    company='Acme AI',
    role='Backend Engineering Intern',
    candidate_name='Alex Kim',
    candidate_background='Python developer interested in automation and AI agents',
    recipient_name='Priya Sharma',
    personalization_note='Company recently launched an AI workflow automation product'
)
d = generate_email(c, config)
print(f'Subject: {d.subject}')
print(f'Body:\n{d.body}')
print(f'Word count: {d.word_count}')
"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 3.1 | `generate_email()` returns `EmailDraft` | must-pass | Test procedure; check type | `isinstance(d, EmailDraft)` |
| 3.2 | Subject is non-empty | must-pass | `len(d.subject) > 0` | `True` |
| 3.3 | Subject mentions role or company | must-pass | `c.role.lower() in d.subject.lower() or c.company.lower() in d.subject.lower()` | `True` |
| 3.4 | Body includes recipient name | must-pass | `c.recipient_name in d.body or "there" in d.body` | `True` |
| 3.5 | Body includes company name | must-pass | `c.company in d.body` | `True` |
| 3.6 | Body includes role | must-pass | `c.role in d.body` | `True` |
| 3.7 | Body includes candidate name | must-pass | `c.candidate_name in d.body` | `True` |
| 3.8 | Body includes candidate background | must-pass | `c.candidate_background in d.body` | `True` |
| 3.9 | Word count ≤ 150 | must-pass | `d.word_count <= 150` | `True` |
| 3.10 | Word count > 0 | must-pass | `d.word_count > 0` | `True` |
| 3.11 | Body contains salutation ("Hi" or "Hello" or "Dear") | should-pass | `"Hi" in d.body or "Hello" in d.body or "Dear" in d.body` | `True` |
| 3.12 | Body contains sign-off ("Best" or "Thanks" or "Sincerely" or "Regards") | should-pass | `"Best" in d.body or "Thanks" in d.body or "Sincerely" in d.body or "Regards" in d.body` | `True` |
| 3.13 | Body contains a clear ask/question | should-pass | `"?" in d.body` or `"would you" in d.body.lower()` or `"open to" in d.body.lower()` | `True` |
| 3.14 | Missing `personalization_note` still generates valid email | must-pass | Run with `personalization_note=None`; check word count | Word count > 20 (minimal viable email) |
| 3.15 | Missing `recipient_name` uses `"there"` | must-pass | Run without `recipient_name`; `"there" in d.body` | `True` |
| 3.16 | Same input produces same output (deterministic) | must-pass | Run generate twice with same contact; compare subject + body | Exact match (no randomness) |
| 3.17 | No hallucinated experience/credentials | should-pass | Check body for "I have experience with" or "I worked at" that doesn't come from `candidate_background` | No false claims |
| 3.18 | `personalization_note` appears in body when provided | should-pass | Run with `personalization_note="recently launched AI product"`; check body | Note content present in body |
| 3.19 | Body is plain text (no HTML) | should-pass | No `<html>`, `<p>`, `<br>` tags in body | Body is plain text |

---

## Phase 4 — Preview + Confirmation (FR3)

### Acceptance criteria

- `preview.py` exports `preview_email(draft, contact)` and `prompt_action()`
- `preview_email()` pretty-prints to terminal
- `prompt_action()` returns one of `"send"`, `"draft"`, `"skip"`
- Invalid inputs re-prompt; Ctrl+C exits gracefully

### Test procedure

Manual test — requires human interaction:

```
python -c "
from models import Contact, EmailDraft
from preview import preview_email, prompt_action

c = Contact(recipient_email='priya@acme.com', company='Acme AI', role='Engineer',
            candidate_name='Alex', candidate_background='Python dev')
d = EmailDraft(subject='Quick note', body='Hi Priya,\n\n...', word_count=42)

preview_email(d, c)
print('Type send/draft/skip:')
action = prompt_action()
print(f'Chosen action: {action}')
"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 4.1 | `preview_email()` runs without error | must-pass | Call with valid `draft` and `contact` | No exception |
| 4.2 | `preview_email()` prints recipient email | should-pass | Check terminal output | Email visible in output |
| 4.3 | `preview_email()` prints company + role | should-pass | Check terminal output | Company and role visible |
| 4.4 | `preview_email()` prints subject | must-pass | Check terminal output | Subject visible |
| 4.5 | `preview_email()` prints body | must-pass | Check terminal output | Body visible |
| 4.6 | `preview_email()` prints word count | should-pass | Check terminal output | Word count visible |
| 4.7 | `prompt_action()` returns `"send"` for "send" input | must-pass | Type `send` + Enter | Returns `"send"` |
| 4.8 | `prompt_action()` returns `"draft"` for "draft" input | must-pass | Type `draft` + Enter | Returns `"draft"` |
| 4.9 | `prompt_action()` returns `"skip"` for "skip" input | must-pass | Type `skip` + Enter | Returns `"skip"` |
| 4.10 | `prompt_action()` is case-insensitive | must-pass | Type `Send`, `SEND`, `Skip`, `SKIP`, `Draft`, `DRAFT` | Same as lowercase |
| 4.11 | Invalid input re-prompts (not crashes) | must-pass | Type `"yes"`, then `"send"` | Returns `"send"` after re-prompt |
| 4.12 | Empty input re-prompts | must-pass | Press Enter, then type `"skip"` | Returns `"skip"` after re-prompt |
| 4.13 | Ctrl+C exits gracefully | must-pass | Press Ctrl+C during prompt | `KeyboardInterrupt` caught; prints "Aborted." or similar; no traceback |
| 4.14 | Visual separation between email fields | should-pass | Inspect terminal output | Fields separated by lines or spacing for readability |

---

## Phase 5 — Email Sender (FR4)

### Acceptance criteria

- `email_sender.py` exports `deliver_email(draft, contact, config, mode)`
- Returns `DeliveryResult`
- Dry-run mode returns success without network
- SMTP mode sends real email or returns clear failure

### Test procedure (dry run — no credentials needed)

```
python -c "
from models import Contact, EmailDraft
from config import load_config
from email_sender import deliver_email

config = load_config()  # DRY_RUN defaults to True
c = Contact(recipient_email='test@example.com', company='TestCo', role='Tester',
            candidate_name='Alex', candidate_background='Python')
d = EmailDraft(subject='Test', body='Hi there', word_count=2)

result = deliver_email(d, c, config, mode='send')
print(f'Status: {result.status}')
print(f'Error: {result.error}')
"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 5.1 | `deliver_email()` returns `DeliveryResult` | must-pass | Dry-run test above | `isinstance(result, DeliveryResult)` |
| 5.2 | `DRY_RUN=true` returns `status="generated"` or `"sent"` | must-pass | Default config; dry-run test | `result.status` is `"generated"` or `"sent"` |
| 5.3 | `DRY_RUN=true` never makes network calls | should-pass | Run with network disconnected | Same result as with network |
| 5.4 | `DRY_RUN=false` with missing SMTP creds fails clearly | must-pass | Create config with `DRY_RUN=false` but empty SMTP vars; call deliver | `result.status == "failed"` and error message mentions missing SMTP config |
| 5.5 | SMTP auth failure returns clear error | must-pass | (If SMTP creds exist) Set wrong password; call deliver | `result.status == "failed"` and error message includes "App Password" or "authentication" |
| 5.6 | `mode="draft"` is accepted | should-pass | Call with `mode="draft"` (dry run) | Returns valid result (not exception) |
| 5.7 | `mode="send"` is accepted | must-pass | Call with `mode="send"` (dry run) | Returns valid result |
| 5.8 | Email `To:` header matches recipient | must-pass | (SMTP test) Check actual sent email or MIME structure | Recipient address present |
| 5.9 | Email `Subject:` header matches draft | must-pass | (SMTP test) Check sent email subject | Matches `draft.subject` |
| 5.10 | Email body matches draft | must-pass | (SMTP test) Check sent body | Matches `draft.body` |
| 5.11 | Email `From:` header uses `SENDER_NAME` | should-pass | (SMTP test) Check From field | Includes sender name from config |
| 5.12 | STARTTLS used on port 587 | should-pass | (SMTP test) Code inspection or SMTP debug output | `starttls()` called |

**Note:** Tests 5.8–5.12 require actual SMTP credentials. For CI/automated testing, skip these when `.env` has no SMTP creds.

---

## Phase 6 — Logger (FR5)

### Acceptance criteria

- `logger.py` exports `append_log(entry, path)`
- Creates CSV with headers if missing
- Appends rows without duplicating headers

### Test procedure

```
python -c "
from logger import append_log
from models import LogEntry
import os

entry = LogEntry(
    timestamp='2026-06-17T12:00:00',
    recipient_email='test@example.com',
    company='TestCo',
    role='Engineer',
    subject='Quick note',
    status='sent'
)
append_log(entry, 'test_log.csv')

# Read back
import csv
with open('test_log.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(f'Rows: {len(rows)}')
    print(f'Columns: {reader.fieldnames}')
    print(f'First row: {rows[0]}')

os.remove('test_log.csv')
"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 6.1 | `append_log()` runs without error | must-pass | Test procedure | No exception |
| 6.2 | New file gets header row | must-pass | After first append, `rows[0]` contains field names | Headers match LogEntry fields |
| 6.3 | Header columns match LogEntry fields | must-pass | `reader.fieldnames` from test | Includes `timestamp`, `recipient_email`, `company`, `role`, `subject`, `status`, `error_message` |
| 6.4 | Data row has correct values | must-pass | Check `rows[0]` | `rows[0]['recipient_email'] == 'test@example.com'` |
| 6.5 | Second append doesn't duplicate headers | must-pass | Append 2 entries, read all rows, check first row contents | First row's `timestamp` doesn't look like "timestamp" (ensure no duplicate header) |
| 6.6 | File created in CWD by default | should-pass | `append_log(entry)` (no path); `os.path.exists('outreach_log.csv')` | `True`; clean up file after test |
| 6.7 | Comma in field value is quoted | should-pass | Create entry with `company="Acme, Inc."`; append; read CSV | Field is `"Acme, Inc."` (quoted) |
| 6.8 | UTF-8 encoding | should-pass | Create entry with unicode (`company="Café"`); read back | Reads correctly as `"Café"` |
| 6.9 | Read-only file raises clear error | should-pass | Make `outreach_log.csv` read-only; try to append | Error message printed, does not crash pipeline |
| 6.10 | ISO-8601 timestamp format | should-pass | Append entry with timestamp from logger; inspect log file | Format like `2026-06-17T12:00:00` |

---

## Phase 7 — Orchestrator (main.py)

### Acceptance criteria

- `main.py` wires the full pipeline: load → generate → preview → confirm → send → log
- Batch summary printed at end
- Hard cap at `MAX_OUTREACH_PER_RUN`
- DrY_RUN=true skips real delivery

### Test procedure

```
# Clean run with dry run
python main.py

# Check log
python -c "
import csv
with open('outreach_log.csv', 'r') as f:
    rows = list(csv.DictReader(f))
    print(f'Total rows: {len(rows)}')
    for r in rows:
        print(f\"  {r['recipient_email']}: {r['status']}\")
"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 7.1 | `main.py` runs end-to-end without error | must-pass | `python main.py` with `DRY_RUN=true` | Exit code 0, no traceback |
| 7.2 | All contacts are processed | must-pass | Run with 5 contacts + `DRY_RUN=true`; check log | 5 rows appended |
| 7.3 | Each contact shows preview before confirmation prompt | must-pass | Observe terminal output during run | Preview printed for each contact |
| 7.4 | User can skip a contact | must-pass | Type `skip` for one contact | Batch summary includes "skipped" count |
| 7.5 | User can confirm a contact | must-pass | Type `send` or `draft` for one contact | Batch summary includes "sent" or "drafted" count |
| 7.6 | Batch summary printed at end | must-pass | Observe terminal after all contacts processed | Summary line with counts |
| 7.7 | Batch summary shows correct totals | must-pass | Skip 2, send 3; verify summary | "3 sent, 0 drafted, 2 skipped, 0 failed" |
| 7.8 | `DRY_RUN=true` never sends real email | must-pass | Run with `DRY_RUN=true`; log status is `"generated"` not `"sent"` | Status = `"generated"` |
| 7.9 | `DRY_RUN=false` with SMTP creds sends email | should-pass | Set `DRY_RUN=false`, configure valid SMTP, run | Emails sent (check inbox) |
| 7.10 | Empty contacts file prints "No contacts" and exits | must-pass | Empty `contacts.json`, run `main.py` | Prints message, exits, log unchanged |
| 7.11 | All contacts skipped prints summary with 0 sent | must-pass | Skip all contacts | Summary: "0 sent, 5 skipped" |
| 7.12 | Check `outreach_log.csv` is created | must-pass | After any run | `outreach_log.csv` exists with data |
| 7.13 | Max outreach cap enforced | must-pass | Set `MAX_OUTREACH_PER_RUN=2`, run with 5 contacts | Only 2 log entries, warning printed |
| 7.14 | Total contacts fewer than cap still processed fully | must-pass | Set `MAX_OUTREACH_PER_RUN=10`, run with 3 contacts | All 3 processed |
| 7.15 | Ctrl+C mid-pipeline prints partial summary | must-pass | Press Ctrl+C during preview of 3rd contact | "Aborted." printed, partial summary shown, no traceback |

---

## Phase 8 — Live Demo Run

### Acceptance criteria

- One real email sent and received
- Screenshot of Sent folder
- `outreach_log.csv` shows status="sent"

### Test procedure

```
# 1. Configure .env
#    DRY_RUN=false
#    SMTP_HOST=smtp.gmail.com
#    SMTP_PORT=587
#    SMTP_USER=your_email@gmail.com
#    SMTP_PASSWORD=your_app_password
#    SENDER_NAME=Your Name
#    SEND_MODE=send

# 2. Update one contact's recipient_email to your own address in contacts.json
# 3. Run
python main.py

# 4. Confirm when prompted
# 5. Verify email in inbox
# 6. Check log
python -c "import csv; [print(r) for r in csv.DictReader(open('outreach_log.csv'))]"
```

### Evaluation table

| # | Check | Type | How to verify | Pass condition |
|---|-------|------|---------------|----------------|
| 8.1 | Email sent without error | must-pass | `python main.py` exit code 0 | Exit code 0 |
| 8.2 | Email arrives in inbox | must-pass | Check Gmail inbox (or recipient address) | Email is received within 2 minutes |
| 8.3 | Email subject matches generated subject | must-pass | Compare sent email subject with terminal preview | Identical |
| 8.4 | Email body matches generated body | must-pass | Compare sent body with preview | Identical |
| 8.5 | From name matches `SENDER_NAME` | should-pass | Check From field in received email | `SENDER_NAME` value appears |
| 8.6 | Log shows status="sent" for that contact | must-pass | `python -c "import csv; r = list(csv.DictReader(open('outreach_log.csv')))[0]; print(r['status'])"` | `"sent"` |
| 8.7 | Restore `DRY_RUN=true` after test | must-pass | Check `.env` after test | `DRY_RUN=true` |

---

## Full Pipeline Integration Test (All Phases Combined)

Run once all phases are complete:

```
# 1. Fresh state
del outreach_log.csv 2>nul

# 2. Dry run first
python main.py

# 3. Verify log
python -c "
import csv
with open('outreach_log.csv') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 5, f'Expected 5 rows, got {len(rows)}'
for r in rows:
    assert r['status'] == 'generated', f'Expected generated, got {r[\"status\"]}'
    assert r['subject'], f'Empty subject for {r[\"recipient_email\"]}'
    assert r['body'], f'Empty body for {r[\"recipient_email\"]}'
print('Integration test PASSED: 5 contacts, all generated, all fields present')
"
```

---

## Regression Checklist (Re-run After Changes)

Use when any module is modified:

| Area | What to re-run |
|------|----------------|
| Config change | Phase 1 tests (1.8–1.12) |
| Input loader change | Phase 2 tests (2.1–2.12) |
| Generator change | Phase 3 tests (3.1–3.19) |
| Preview change | Phase 4 tests (4.1–4.14) |
| Sender change | Phase 5 tests (5.1–5.7) |
| Logger change | Phase 6 tests (6.1–6.10) |
| Orchestrator change | Full pipeline integration test |
| Any change | `python main.py` (must not crash) |
