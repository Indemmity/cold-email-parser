from src.models import Contact, EmailDraft


def preview_email(draft: EmailDraft, contact: Contact) -> None:
    print("=" * 60)
    print(f"Company: {contact.company}")
    print(f"Role:    {contact.role}")
    print(f"To:      {contact.recipient_name} <{contact.recipient_email}>")
    print("-" * 60)
    print(f"Subject: {draft.subject}")
    print("-" * 60)
    print(draft.body)
    print("-" * 60)
    print(f"Word count: {draft.word_count}")
    print("=" * 60)


def prompt_action() -> str:
    while True:
        choice = input("Send this email? (send/draft/skip): ").strip().lower()
        if choice in ("send", "draft", "skip"):
            return choice
        print("Invalid input. Enter 'send', 'draft', or 'skip'.")
