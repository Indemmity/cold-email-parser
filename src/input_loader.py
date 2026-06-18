import json
import re

from src.models import Contact


def load_targets(path: str) -> list[Contact]:
    with open(path, "r") as f:
        records = json.load(f)

    contacts = []
    for i, rec in enumerate(records):
        errors = _validate(rec, i)
        if errors:
            for err in errors:
                print(f"Warning: record {i} skipped — {err}")
            continue

        contacts.append(
            Contact(
                recipient_email=rec["recipient_email"],
                company=rec["company"],
                role=rec["role"],
                candidate_name=rec["candidate_name"],
                candidate_background=rec["candidate_background"],
                recipient_name=rec.get("recipient_name") or "there",
                job_url=rec.get("job_url"),
                portfolio_url=rec.get("portfolio_url"),
                personalization_note=rec.get("personalization_note"),
                linkedin_url=rec.get("linkedin_url"),
                resume_link=rec.get("resume_link"),
            )
        )

    return contacts


def _validate(rec: dict, index: int) -> list[str]:
    errors = []

    required_fields = [
        ("recipient_email", "recipient_email"),
        ("company", "company"),
        ("role", "role"),
        ("candidate_name", "candidate_name"),
        ("candidate_background", "candidate_background"),
    ]

    for field, label in required_fields:
        value = rec.get(field)
        if not value or not str(value).strip():
            errors.append(f"missing required field '{label}'")

    email = rec.get("recipient_email", "")
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append(f"invalid email format '{email}'")

    return errors
