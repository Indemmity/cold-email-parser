from __future__ import annotations

from datetime import datetime, timezone

from src.config import load_config
from src.email_generator import generate_email
from src.email_sender import deliver_email
from src.input_loader import load_targets
from src.logger import append_log
from src.models import Contact, EmailDraft, LogEntry
from src.preview import preview_email, prompt_action


def run_outreach_pipeline() -> None:
    config = load_config()

    contacts = load_targets(config.input_path or "contacts.json")
    contacts = contacts[: config.max_outreach_per_run]

    counts: dict[str, int] = {"sent": 0, "drafted": 0, "skipped": 0, "failed": 0}

    try:
        for contact in contacts:
            draft = generate_email(contact)
            preview_email(draft, contact)

            action = prompt_action()
            if action == "skip":
                _log(contact, draft, "skipped")
                counts["skipped"] += 1
                continue

            if config.dry_run:
                _log(contact, draft, "generated")
                counts["drafted"] += 1
                continue

            result = deliver_email(draft, contact, config)
            _log(contact, draft, result.status, result.error)
            counts[result.status] = counts.get(result.status, 0) + 1

    except KeyboardInterrupt:
        print("\nAborted.")

    _print_summary(counts)


def _log(
    contact: Contact, draft: EmailDraft, status: str, error: str | None = None
) -> None:
    append_log(
        LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            recipient_email=contact.recipient_email,
            company=contact.company,
            role=contact.role,
            subject=draft.subject,
            status=status,
            error_message=error or "",
            word_count=draft.word_count,
            job_url=contact.job_url,
        )
    )


def _print_summary(counts: dict[str, int]) -> None:
    total = sum(counts.values())
    parts = [f"{v} {k}" for k, v in counts.items() if v > 0]
    print("\n" + "=" * 40)
    print(f"Batch complete — {total} contacts processed")
    if parts:
        print(" | ".join(parts))
    print("=" * 40)


if __name__ == "__main__":
    run_outreach_pipeline()
