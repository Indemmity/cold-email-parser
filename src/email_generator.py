from src.models import Contact, EmailDraft


def generate_email(contact: Contact) -> EmailDraft:
    hook = _build_hook(contact)
    portfolio_line = f"\n{contact.portfolio_url}" if contact.portfolio_url else ""

    body = f"""Hi {contact.recipient_name},

{hook}

I'm {contact.candidate_name}, and I've been working with {contact.candidate_background}. The {contact.role} role at {contact.company} caught my attention because it aligns closely with what I enjoy building.

Would you be open to a brief chat about how my background fits the role?{portfolio_line}

Best,
{contact.candidate_name}"""

    word_count = len(body.split())
    if word_count > 150:
        print(f"Warning: email to {contact.recipient_email} is {word_count} words (>150)")

    subject = f"Quick note on the {contact.role} role"

    return EmailDraft(subject=subject, body=body.strip(), word_count=word_count)


def _build_hook(contact: Contact) -> str:
    if contact.personalization_note:
        return f"I recently came across {contact.company} and saw that {contact.personalization_note}."
    return f"I've been following {contact.company}'s work and noticed you're hiring for a {contact.role}."
