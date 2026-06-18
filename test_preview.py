from src.input_loader import load_targets
from src.email_generator import generate_email
from src.preview import preview_email, prompt_action

c = load_targets("contacts.json")[0]
d = generate_email(c)
preview_email(d, c)
action = prompt_action()
print(f"You chose: {action}")
