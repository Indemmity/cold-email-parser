from dataclasses import dataclass


@dataclass
class Contact:
    recipient_email: str
    company: str
    role: str
    candidate_name: str
    candidate_background: str
    recipient_name: str | None = None
    job_url: str | None = None
    portfolio_url: str | None = None
    personalization_note: str | None = None
    linkedin_url: str | None = None
    resume_link: str | None = None


@dataclass
class EmailDraft:
    subject: str
    body: str
    word_count: int


@dataclass
class LogEntry:
    timestamp: str
    recipient_email: str
    company: str
    role: str
    subject: str
    status: str
    error_message: str = ""
    word_count: int = 0
    job_url: str | None = None


@dataclass
class DeliveryResult:
    status: str  # "drafted" | "sent" | "failed"
    provider_message_id: str | None = None
    error: str | None = None
