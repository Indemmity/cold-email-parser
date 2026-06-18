from __future__ import annotations

import csv
from pathlib import Path

from src.models import LogEntry

LOG_COLUMNS = [
    "timestamp",
    "recipient_email",
    "company",
    "role",
    "subject",
    "status",
    "error_message",
    "word_count",
    "job_url",
]

DEFAULT_LOG_PATH = "outreach_log.csv"


def append_log(entry: LogEntry, path: str = DEFAULT_LOG_PATH) -> None:
    """Append a LogEntry to a CSV file. Creates the file with headers if missing."""
    file_exists = Path(path).is_file()

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(LOG_COLUMNS)

        writer.writerow(
            [
                entry.timestamp,
                entry.recipient_email,
                entry.company,
                entry.role,
                entry.subject,
                entry.status,
                entry.error_message,
                entry.word_count,
                entry.job_url or "",
            ]
        )
