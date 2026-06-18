"""Streamlit UI for The Closer — cold email pipeline with human review."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from src.config import load_config
from src.email_generator import generate_email
from src.email_sender import deliver_email
from src.input_loader import load_targets as _load_targets
from src.logger import LOG_COLUMNS, DEFAULT_LOG_PATH, append_log
from src.models import Contact, LogEntry

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="The Closer — Outreach Pipeline",
    page_icon="✉️",
    layout="wide",
)

# ── Session state ────────────────────────────────────────────────────────────

_DEFAULTS = {
    "contacts": [],
    "drafts": {},
    "results": {},
    "current_idx": 0,
    "config": None,
    "log_df": None,
    "processed_contacts": set(),
}

for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.config is None:
    st.session_state.config = load_config()


# ── Helpers ──────────────────────────────────────────────────────────────────

def status_emoji(status: str) -> str:
    return {
        "sent": "✅", "drafted": "📄", "generated": "📄",
        "skipped": "⏭️", "failed": "❌", "pending": "⏳",
    }.get(status, "⏳")


def get_contact_status(idx: int) -> str:
    if idx in st.session_state.results:
        return st.session_state.results[idx]["status"]
    return "pending"


def load_contacts_from_json(content: bytes | str) -> list[Contact]:
    """Load contacts from raw JSON content with Streamlit warning handling."""
    import io
    records = json.loads(content) if isinstance(content, bytes) else json.loads(content)
    contacts: list[Contact] = []
    for i, rec in enumerate(records):
        errors = _validate_contact(rec, i)
        if errors:
            for err in errors:
                st.warning(f"Record {i} skipped — {err}")
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


def _validate_contact(rec: dict, index: int) -> list[str]:
    import re
    errors = []
    required = [
        ("recipient_email", "recipient_email"),
        ("company", "company"),
        ("role", "role"),
        ("candidate_name", "candidate_name"),
        ("candidate_background", "candidate_background"),
    ]
    for field, label in required:
        value = rec.get(field)
        if not value or not str(value).strip():
            errors.append(f"missing required field '{label}'")
    email = rec.get("recipient_email", "")
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append(f"invalid email format '{email}'")
    return errors


def reset_pipeline() -> None:
    st.session_state.drafts = {}
    st.session_state.results = {}
    st.session_state.current_idx = 0
    st.session_state.processed_contacts = set()


def canonical_log_path() -> str:
    """Return the log path from config, or default."""
    return getattr(st.session_state.config, "log_path", None) or DEFAULT_LOG_PATH


def load_log_df() -> pd.DataFrame | None:
    path = canonical_log_path()
    if Path(path).is_file():
        try:
            return pd.read_csv(path)
        except Exception:
            return None
    return None


def log_attempt(contact: Contact, draft, status: str, error: str | None) -> None:
    """Log an outreach attempt to the CSV file."""
    try:
        append_log(LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            recipient_email=contact.recipient_email,
            company=contact.company,
            role=contact.role,
            subject=draft.subject,
            status=status,
            error_message=error or "",
            word_count=draft.word_count,
            job_url=contact.job_url,
        ))
    except Exception as e:
        st.warning(f"Failed to write log entry: {e}")


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ The Closer")

    config = st.session_state.config

    # ── Config section ──
    with st.expander("Settings", expanded=False):
        config.dry_run = st.checkbox("Dry Run (no actual send)", value=config.dry_run)
        config.max_outreach_per_run = st.number_input(
            "Max contacts per run",
            min_value=1, max_value=50,
            value=config.max_outreach_per_run,
        )
        with st.container(border=True):
            st.caption("SMTP")
            config.smtp_host = st.text_input("Host", value=config.smtp_host, key="smtp_host")
            config.smtp_port = st.number_input(
                "Port", min_value=1, max_value=65535, value=config.smtp_port, key="smtp_port",
            )
            config.smtp_user = st.text_input("User", value=config.smtp_user, key="smtp_user")
            config.smtp_password = st.text_input(
                "Password", type="password", value=config.smtp_password, key="smtp_password",
            )
            config.sender_name = st.text_input(
                "Sender Name", value=config.sender_name, key="sender_name",
            )

    # ── File load section ──
    st.divider()
    st.subheader("📁 Contacts")

    uploaded_file = st.file_uploader(
        "Upload contacts.json",
        type=["json"],
        label_visibility="collapsed",
    )

    col_left, col_right = st.columns(2)
    with col_left:
        load_default = st.button("📥 Default", use_container_width=True)
    with col_right:
        load_uploaded = st.button("📤 Uploaded", use_container_width=True)

    if load_default:
        try:
            contacts = _load_targets("contacts.json")
            st.session_state.contacts = contacts[: config.max_outreach_per_run]
            reset_pipeline()
            st.rerun()
        except FileNotFoundError:
            st.error("contacts.json not found in project root.")

    if load_uploaded and uploaded_file is not None:
        try:
            contacts = load_contacts_from_json(uploaded_file.getvalue())
            st.session_state.contacts = contacts[: config.max_outreach_per_run]
            reset_pipeline()
            st.rerun()
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")

    # ── Pipeline controls ──
    if st.session_state.contacts:
        st.divider()
        st.subheader("🔄 Pipeline")

        if st.button("Reset Pipeline", use_container_width=True):
            reset_pipeline()
            st.rerun()

    # ── Summary widget ──
    if st.session_state.results:
        st.divider()
        st.subheader("📈 Summary")
        statuses = [r["status"] for r in st.session_state.results.values()]
        sent = statuses.count("sent")
        drafted = statuses.count("drafted") + statuses.count("generated")
        skipped = statuses.count("skipped")
        failed = statuses.count("failed")
        pending = len(st.session_state.contacts) - len(st.session_state.results)

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.metric("Sent", sent)
            st.metric("Drafted", drafted)
        with mcol2:
            st.metric("Skipped", skipped)
            st.metric("Failed", failed)
        if pending > 0:
            st.caption(f"{pending} pending")


# ── Main content ─────────────────────────────────────────────────────────────

contacts = st.session_state.contacts
drafts = st.session_state.drafts
results = st.session_state.results

tab_contacts, tab_pipeline, tab_log = st.tabs(["📋 Contacts", "✉️ Pipeline", "📊 Log"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Contacts
# ═══════════════════════════════════════════════════════════════════════════════

with tab_contacts:
    if not contacts:
        st.info("No contacts loaded. Use the sidebar to load contacts from a file.")
        st.stop()

    st.subheader(f"Loaded {len(contacts)} contacts")

    table_rows = []
    for i, c in enumerate(contacts):
        status = get_contact_status(i)
        emoji = status_emoji(status)
        draft = drafts.get(i)
        table_rows.append({
            "#": i + 1,
            "Status": f"{emoji} {status}",
            "Name": c.recipient_name or "there",
            "Email": c.recipient_email,
            "Company": c.company,
            "Role": c.role,
            "Subject": draft.subject if draft else "—",
        })

    df_contacts = pd.DataFrame(table_rows)
    st.dataframe(
        df_contacts,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Subject": st.column_config.TextColumn("Subject", width="large"),
        },
    )

    # Quick actions row
    st.divider()
    action_cols = st.columns(4)
    with action_cols[0]:
        if st.button("Generate All Drafts", use_container_width=True, type="primary"):
            for i, c in enumerate(contacts):
                if i not in drafts:
                    drafts[i] = generate_email(c)
            st.rerun()
    with action_cols[1]:
        if st.button("Reset All Drafts", use_container_width=True):
            st.session_state.drafts = {}
            st.rerun()
    with action_cols[2]:
        if st.button("Skip All Pending", use_container_width=True):
            now = datetime.now(timezone.utc).isoformat()
            for i, c in enumerate(contacts):
                if i not in results:
                    results[i] = {"status": "skipped", "error": None}
                    draft = drafts.get(i) or generate_email(c)
                    append_log(LogEntry(
                        timestamp=now,
                        recipient_email=c.recipient_email,
                        company=c.company,
                        role=c.role,
                        subject=draft.subject,
                        status="skipped",
                        error_message="",
                        word_count=draft.word_count,
                        job_url=c.job_url,
                    ))
            st.rerun()
    with action_cols[3]:
        if st.button("Export Contacts CSV", use_container_width=True):
            csv = df_contacts.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download CSV", data=csv, file_name="contacts_status.csv", mime="text/csv",
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

with tab_pipeline:
    if not contacts:
        st.info("No contacts loaded. Use the sidebar to load contacts from a file.")
        st.stop()

    total = len(contacts)
    idx = st.session_state.current_idx

    # Bounds check
    if idx >= total:
        idx = total - 1
        st.session_state.current_idx = idx

    # Progress
    processed_count = len(results)
    st.progress(processed_count / total, text=f"{processed_count} / {total} contacts processed")

    # ── Navigation ──
    nav_cols = st.columns([1, 3, 1])
    with nav_cols[0]:
        if st.button("◀ Previous", use_container_width=True, disabled=(idx <= 0)):
            st.session_state.current_idx = max(0, idx - 1)
            st.rerun()
    with nav_cols[1]:
        st.markdown(
            f"<h4 style='text-align:center; margin:0;'>Contact {idx + 1} of {total}</h4>",
            unsafe_allow_html=True,
        )
    with nav_cols[2]:
        if st.button("Next ▶", use_container_width=True, disabled=(idx >= total - 1)):
            st.session_state.current_idx = min(total - 1, idx + 1)
            st.rerun()

    st.divider()

    # ── Contact info ──
    contact = contacts[idx]

    info_cols = st.columns(3)
    with info_cols[0]:
        st.text_input("Name", value=contact.recipient_name or contact.recipient_email, disabled=True)
    with info_cols[1]:
        st.text_input("Email", value=contact.recipient_email, disabled=True)
    with info_cols[2]:
        st.text_input("Company / Role", value=f"{contact.company} — {contact.role}", disabled=True)

    if contact.job_url:
        st.markdown(f"🔗 [Job posting]({contact.job_url})")
    if contact.linkedin_url:
        st.markdown(f"🔗 [LinkedIn]({contact.linkedin_url})")
    if contact.personalization_note:
        st.info(f"💡 Personalization note: {contact.personalization_note}")

    # ── Generate draft ──
    current_status = get_contact_status(idx)
    draft = drafts.get(idx)

    if draft is None:
        if st.button("✍️ Generate Email", type="primary", use_container_width=True):
            drafts[idx] = generate_email(contact)
            st.rerun()
    else:
        # ── Email preview ──
        st.divider()
        st.subheader(f"✉️ {draft.subject}")
        st.text_area(
            "Email body",
            value=draft.body,
            height=350,
            disabled=True,
            label_visibility="collapsed",
        )
        st.caption(f"Word count: {draft.word_count}")

        # ── Action buttons ──
        st.divider()
        st.markdown("**Action**")

        already_processed = idx in results
        if already_processed:
            st.info(
                f"This contact has already been **{results[idx]['status']}**. "
                "Use Reset Pipeline to reprocess."
            )
        else:
            act_cols = st.columns(3)
            with act_cols[0]:
                if st.button("✅ Send", use_container_width=True, type="primary"):
                    if config.dry_run:
                        result = deliver_email(draft, contact, config)
                        results[idx] = {"status": result.status, "error": result.error}
                        log_attempt(contact, draft, result.status, result.error)
                        st.rerun()
                    else:
                        result = deliver_email(draft, contact, config)
                        results[idx] = {"status": result.status, "error": result.error}
                        log_attempt(contact, draft, result.status, result.error)
                        st.rerun()
            with act_cols[1]:
                if st.button("📄 Draft (log only)", use_container_width=True):
                    results[idx] = {"status": "drafted", "error": None}
                    log_attempt(contact, draft, "drafted", None)
                    st.rerun()
            with act_cols[2]:
                if st.button("⏭️ Skip", use_container_width=True):
                    results[idx] = {"status": "skipped", "error": None}
                    log_attempt(contact, draft, "skipped", None)
                    st.rerun()

    # ── Show result if processed ──
    if idx in results:
        res = results[idx]
        status = res["status"]
        emoji = status_emoji(status)
        if status == "sent":
            st.success(f"{emoji} Email sent successfully!")
        elif status in ("drafted", "generated"):
            st.info(f"{emoji} Email logged as '{status}'.")
        elif status == "skipped":
            st.warning(f"{emoji} Contact skipped.")
        elif status == "failed":
            st.error(f"{emoji} Failed: {res.get('error', 'Unknown error')}")

    # ── Jump to next unprocessed ──
    if idx < total - 1 and idx in results:
        if st.button("→ Next Unprocessed Contact", use_container_width=True):
            # Find next unprocessed
            for i in range(idx + 1, total):
                if i not in results:
                    st.session_state.current_idx = i
                    st.rerun()
            st.info("All contacts have been processed!")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Log
# ═══════════════════════════════════════════════════════════════════════════════

with tab_log:
    st.subheader("Outreach Log")

    log_path = canonical_log_path()
    log_df = load_log_df()

    if log_df is not None and not log_df.empty:
        # Summary stats
        status_counts = log_df["status"].value_counts()
        stat_cols = st.columns(len(status_counts))
        for col, (status, count) in zip(stat_cols, status_counts.items()):
            emoji = status_emoji(status)
            col.metric(f"{emoji} {status}", count)

        st.divider()
        st.dataframe(log_df, use_container_width=True, hide_index=True)

        csv_data = log_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Log CSV",
            data=csv_data,
            file_name="outreach_log.csv",
            mime="text/csv",
        )

        # Refresh button
        if st.button("🔄 Refresh Log"):
            st.rerun()
    else:
        st.info("No log entries yet. Run the pipeline to generate outreach log data.")


# ── End of file ──
