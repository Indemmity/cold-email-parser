import os

from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class AppConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    sender_name: str = ""
    dry_run: bool = True
    send_mode: str = "draft"
    max_outreach_per_run: int = 5
    input_path: str | None = None


def _get_val(key: str, default: str) -> str:
    """Read from Streamlit secrets first, then os.environ, then default."""
    try:
        import streamlit as st  # type: ignore[import-untyped]

        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)


def load_config(path: str | None = None) -> AppConfig:
    load_dotenv(path, override=True)

    return AppConfig(
        smtp_host=_get_val("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(_get_val("SMTP_PORT", "587")),
        smtp_user=_get_val("SMTP_USER", ""),
        smtp_password=_get_val("SMTP_PASSWORD", ""),
        sender_name=_get_val("SENDER_NAME", ""),
        dry_run=_get_val("DRY_RUN", "true").lower() == "true",
        send_mode=_get_val("SEND_MODE", "draft"),
        max_outreach_per_run=int(_get_val("MAX_OUTREACH_PER_RUN", "5")),
        input_path=_get_val("INPUT_PATH", "") or None,
    )
