# Edge Cases: The Closer

Covers all edge cases by module. Each case includes the category, trigger, expected behavior, and severity.

---

## 1. Config (`config.py`)

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 1.1 | `.env` file missing | No `.env` in project root | `load_config()` uses all defaults, does not crash | Medium |
| 1.2 | Required SMTP vars missing when sending | `DRY_RUN=false` but `SMTP_USER` / `SMTP_PASSWORD` empty | `deliver_email()` returns `DeliveryResult(status="failed", error="SMTP_USER not configured")` — never crash with vague error | High |
| 1.3 | `SMTP_PORT` set to non-integer string | `SMTP_PORT=abc` in `.env` | `load_config()` raises `ValueError` with clear message, or falls back to default 587 with warning | Medium |
| 1.4 | `MAX_OUTREACH_PER_RUN` set to 0 or negative | `MAX_OUTREACH_PER_RUN=0` or `-1` | Default to 5 with a warning; never send 0 or negative | Medium |
| 1.5 | `DRY_RUN` typo or invalid value | `DRY_RUN=maybe` | Treat as truthy only if lowercase `"true"`; anything else → `false` (safe default is `true` when var is missing, but explicit `false` requires exact match) | Low |
| 1.6 | `SEND_MODE` invalid value | `SEND_MODE=pigeon` | Default to `"draft"` with warning; never use unhandled mode | Low |

---

## 2. Input Loader (`input_loader.py` + `contacts.json`)

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 2.1 | `contacts.json` file not found | File missing or wrong path | `load_targets()` raises `FileNotFoundError` with clear path message | High |
| 2.2 | `contacts.json` is malformed JSON | Syntax error, trailing comma | Catch `json.JSONDecodeError`, raise clear error with file + line info | High |
| 2.3 | `contacts.json` is not a list | Contains a single object `{}` instead of `[{...}]` | Wrap in list, or raise clear type error | Medium |
| 2.4 | Empty contacts list | `[]` | `load_targets()` returns `[]`, `main.py` prints "No contacts to process" and exits cleanly | Medium |
| 2.5 | Record missing `recipient_email` | Field absent or empty string | Skip record, log warning to terminal, continue | High |
| 2.6 | Record has invalid email format | `"not-an-email"` or `""` | Skip record with warning "Invalid email: not-an-email" | High |
| 2.7 | Record missing `company` | Field absent | Skip record, warn | High |
| 2.8 | Record missing `role` | Field absent | Skip record, warn | High |
| 2.9 | Record missing `candidate_name` | Field absent | Skip record, warn | High |
| 2.10 | Record missing `candidate_background` | Field absent | Skip record, warn | High |
| 2.11 | `recipient_name` missing | Field absent | Default to `"there"` (email opens with "Hi there,") | Low |
| 2.12 | `personalization_note` missing | Field absent | Generator uses company + role fallback hook | Low |
| 2.13 | Extra whitespace in string fields | `"  Priya  "` or `"  "` | Strip whitespace; after strip, treat empty string as missing | Medium |
| 2.14 | Very long field values | `candidate_background` is 10,000 chars | No truncation in MVP; word-count check after generation may catch oversized bodies | Low |
| 2.15 | Unicode/special characters in names | `candidate_name: "Håkon Ægir"` or `recipient_name: "José"` | Pass through as-is; no sanitization needed for plain-text email | Low |
| 2.16 | HTML/control characters in fields | `candidate_background: "<script>alert('xss')</script>"` | Pass through as-is (plain-text email has no HTML rendering risk) | Low |
| 2.17 | Invalid URL fields | `portfolio_url: "not a url"` | Basic URL validation check; warn but do not skip — still include in email | Low |
| 2.18 | Duplicate records | Same `recipient_email` + `company` + `role` | Process both (MVP has no dedup); stretch: filter duplicates | Low |
| 2.19 | CSV input with wrong column headers | `contacts.csv` has `Name,Email` instead of `recipient_name,recipient_email` | Raise clear error listing expected columns (stretch feature) | N/A for MVP |
| 2.20 | All records invalid | Every record missing required fields | Return `[]`, pipeline prints "No valid contacts to process" | Medium |

---

## 3. Email Generator (`email_generator.py`)

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 3.1 | All required fields present, no optional fields | Only 5 required fields → minimal email | Generate valid email using company+role fallback for hook; `recipient_name` defaults to `"there"` | Low |
| 3.2 | Word count exceeds 150 | Long `candidate_background` or `personalization_note` | Print warning after generation: "Warning: email is 187 words (max 150)". Do not block in MVP — just warn | Medium |
| 3.3 | `personalization_note` empty, company+role generic | `company: "Company"`, `role: "Role"` | Fallback hook is weak; generator should still produce a reasonable sentence like "I noticed Company is hiring for a Role position." | Low |
| 3.4 | `candidate_background` very short | `"Student"` or `"N/A"` | Still produces valid email; introduction section may be thin but functional | Low |
| 3.5 | Template variable contains special regex/$ characters | `role: "Software Engineer ($150k+ bonus)"` | f-string handles it (no regex involved). No escaping needed for Python f-strings | Low |
| 3.6 | Newlines in field values | `candidate_background: "Python dev\nInterested in AI"` | Embedded in body text; may break email formatting but not dangerous | Low |
| 3.7 | Multiple personalization sources conflict | `personalization_note` mentions product X, but `company` does AI — contradiction | Generator trusts provided fields; no cross-check in MVP | Low |
| 3.8 | Same company, multiple roles | Two contacts for Acme AI with different roles | Generator produces distinct emails per role (good — expected behavior) | Low |

---

## 4. Preview + Confirmation (`preview.py`)

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 4.1 | User enters invalid action | `"yes"`, `"y"`, `"send it"`, `"x"` | Re-prompt with valid options: `"Type 'send', 'draft', or 'skip':"`. Do not crash | Medium |
| 4.2 | User enters empty input | Presses Enter with no text | Re-prompt | Medium |
| 4.3 | User enters case variations | `"Send"`, `"SEND"`, `"Skip"` | Accept case-insensitively (`.lower().strip()`) | Low |
| 4.4 | User enters Ctrl+C (KeyboardInterrupt) | Interrupt during prompt | Catch `KeyboardInterrupt`, print "\nAborted.", exit gracefully — no traceback | High |
| 4.5 | User enters Ctrl+D (EOF) | EOF during prompt | Treat as skip or abort; exit gracefully | Medium |
| 4.6 | Very long subject line overflows terminal | Subject > 80 characters | Print normally; terminal handles word-wrap. No truncation needed | Low |
| 4.7 | Email body has no newline at end | Generator output lacks trailing newline | Add trailing newline in preview for clean display | Low |
| 4.8 | User skips every contact | Presses skip on all | Pipeline completes, batch summary shows all skipped | Low |

---

## 5. Email Sender (`email_sender.py`)

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 5.1 | SMTP connection refused | Wrong host/port, server down | `DeliveryResult(status="failed", error="Connection refused to smtp.gmail.com:587")` | High |
| 5.2 | SMTP authentication failure | Wrong password, Gmail App Password expired | `DeliveryResult(status="failed", error="Authentication failed. If using Gmail, generate a new App Password at https://myaccount.google.com/apppasswords")` | High |
| 5.3 | Network timeout | Slow/no internet | `DeliveryResult(status="failed", error="Connection timed out after 30s")` (set socket timeout) | High |
| 5.4 | Recipient email rejected by server | Invalid domain (`user@nonexistent.xyz`), server returns 550 | `DeliveryResult(status="failed", error="Server rejected: 550 ...")` | High |
| 5.5 | `DRY_RUN=true` with no SMTP config | Default config — no vars set | Dry-run returns success without checking SMTP at all. This must never fail. | High |
| 5.6 | `DRY_RUN=false` with no SMTP config | User sets DRY_RUN=false but hasn't set SMTP vars | Fail early in `deliver_email()` with clear message: "SMTP_USER and SMTP_PASSWORD required when DRY_RUN=false" | High |
| 5.7 | Email body with only ASCII text | Normal case | Works fine with SMTP | Low |
| 5.8 | Email body with Unicode text | Non-ASCII characters in body | Encode as UTF-8; `smtplib` handles this with `msg.set_charset("utf-8")` or using `email.message` properly | Medium |
| 5.9 | Sending to yourself | `recipient_email` same as `SMTP_USER` | Works fine (intentional — used for testing). No special handling needed | Low |
| 5.10 | Sending multiple emails rapidly | 5 contacts, user confirms all | Send in sequence with no delay; SMTP handles this. No rate limiting in MVP | Low |
| 5.11 | SMTP email size limit | Body extremely large (~25MB) | Not applicable for MVP (emails are <150 words, <1KB) | Low |
| 5.12 | Sender name has special characters | `SENDER_NAME: "O'Brien"` | Passed as display name in email headers; ensure proper header encoding | Low |
| 5.13 | TLS/STARTTLS failure | Server doesn't support STARTTLS | Fall back to plain SMTP or fail with clear error | Medium |

---

## 6. Logger (`logger.py`)

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 6.1 | `outreach_log.csv` doesn't exist | First run | Create file with headers, append first row | High |
| 6.2 | `outreach_log.csv` exists from previous run | Second run | Append new rows; do not overwrite or duplicate headers | High |
| 6.3 | `outreach_log.csv` read-only | File permissions block write | `append_log()` catches `PermissionError`, prints error to terminal, continues pipeline | Medium |
| 6.4 | Parent directory missing | Current working directory is unexpected | Log to `outreach_log.csv` in CWD; if CWD not writable, raise clear error | Low |
| 6.5 | Unicode in log fields | `company: "Café Zürich"` | Write as UTF-8; CSV module handles it with `encoding="utf-8"` | Low |
| 6.6 | Comma in a field value | `company: "Acme, Inc."` | Quote properly; `csv.writer` handles quoting automatically | Medium |
| 6.7 | Newline in a field value | Multi-line error message | `csv.writer` quotes fields containing newlines automatically | Low |
| 6.8 | Very large log file | 10,000+ rows over time | Appending is O(1); no issue for MVP. Stretch: log rotation | Low |
| 6.9 | Timestamp formatting | System locale differences | Use ISO-8601 via `datetime.now(timezone.utc).isoformat()` — locale-independent | Medium |
| 6.10 | Concurrent writes (unlikely) | Two process instances writing simultaneously | Not handled in MVP. Stretch: file lock | Low |
| 6.11 | Status contains unexpected value | Bug in orchestrator passes `"undefined"` | Write it as-is; validation is caller's responsibility | Low |

---

## 7. Orchestrator / Pipeline (`main.py`)

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 7.1 | All contacts valid, user confirms all | Happy path | All 5 processed end-to-end, batch summary shows 5 sent/drafted | Low |
| 7.2 | Some contacts invalid, some valid | Mix of good and bad records | Invalid records skipped with warning; valid ones processed normally | Medium |
| 7.3 | All contacts invalid / empty list | Input returns `[]` | Print "No valid contacts to process.", exit cleanly | Medium |
| 7.4 | User skips all contacts | Skips every prompt | Batch summary: 0 sent, 0 drafted, 5 skipped, 0 failed | Low |
| 7.5 | User sends some, skips some | Mixed actions | Batch summary reflects the mix correctly | Low |
| 7.6 | Sender fails mid-batch | Contact 1 succeeds, contact 2 fails | Log failed status for contact 2, continue with contact 3. Print summary with failures at end | High |
| 7.7 | More contacts than `MAX_OUTREACH_PER_RUN` | 10 contacts file, cap at 5 | Process only first 5, print warning "Reached max 5 contacts for this run. Processed 5 of 10." | Medium |
| 7.8 | `MAX_OUTREACH_PER_RUN` exceeds actual contacts | Cap at 10, only 3 contacts | All 3 processed; cap doesn't truncate short lists | Low |
| 7.9 | `KeyboardInterrupt` during pipeline processing | User presses Ctrl+C mid-batch | Stop processing, print partial summary of what was done so far, exit cleanly | High |
| 7.10 | No input file path configured | `INPUT_PATH` not set, no default fallback | Attempt `contacts.json` in CWD; if missing, raise clear error | Medium |
| 7.11 | Pipeline run with no changes from previous run | Same contacts file, second run | Processes all contacts again; log appends new rows (duplication by design in MVP) | Low |

---

## 8. Safety / Ethics

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 8.1 | User sends without reviewing | Premature confirmation | Impossible by design — `preview_and_confirm()` runs before `deliver_email()` | Medium |
| 8.2 | Recipient's email bounces back | Invalid recipient domain | Logged as `failed`; no retry in MVP | Medium |
| 8.3 | User accidentally sends to wrong person | Typo in recipient_email | User error; system can't prevent. Log provides audit trail | Low |
| 8.4 | Email content reveals fabricated experience | Template interpolates unverified claims | No LLM in MVP; template only uses provided `candidate_background`. User controls input | Medium |
| 8.5 | Intentionally adversarial input | `recipient_email: "hacker@malicious.com; DROP TABLE users"` | No SQL or shell in pipeline. Plain-text only; no injection risk | Low |

---

## 9. Cross-Module / Integration

| # | Edge case | Trigger | Expected behavior | Sev |
|---|-----------|---------|-------------------|-----|
| 9.1 | Generator succeeds → preview succeeds → sender fails → logger writes | Partial failure on one contact | Log status=`"failed"` with error message. Pipeline continues to next contact | High |
| 9.2 | Config loaded with unexpected types | `MAX_OUTREACH_PER_RUN="five"` instead of numeric | `load_config()` validates types on load; raises ValueError | Medium |
| 9.3 | Pipeline runs from wrong directory | User runs `python the-closer/main.py` from parent folder | CWD is parent folder; contacts.json and .env resolved relative to CWD, not script location. Use `os.path.dirname(__file__)` for resource paths, or document that user must `cd the-closer` | Medium |
| 9.4 | Encoding mismatch across modules | System default encoding is not UTF-8 (Windows) | Explicitly use `encoding="utf-8"` on all file operations | Medium |
