import hashlib
import json
import os
import re
import sys

from scraper import fetch_entries
from notifier import create_notifier

STATE_FILE = os.path.join(os.path.dirname(__file__), "last_seen.json")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def main():
    entries = fetch_entries()

    if not entries:
        print("No s'han trobat entrades.")
        return

    latest = entries[0]
    current_hash = hashlib.sha256(latest.title.encode()).hexdigest()

    state = load_state()
    last_hash = state.get("last_hash")

    if current_hash == last_hash:
        print(f"Sense canvis. Última entrada: {latest.title}")
        return

    print(f"Nova entrada detectada: {latest.title}")

    # First run: save state without notifying
    if last_hash is None:
        print("Primera execució, guardant estat inicial.")
        save_state({"last_hash": current_hash, "last_title": latest.title})
        return

    notifier = create_notifier()

    # Split "Divendres 30, 11h. La Nit de Castells..." into prefix + rest
    match = re.match(r"^(\w+ \d+,\s*\d+h\.)\s*(.+)$", latest.title)
    if match:
        time_prefix = match.group(1)  # "Divendres 30, 11h."
        title = match.group(2)         # "La Nit de Castells..."
        body = time_prefix
        if latest.excerpt:
            body += " " + latest.excerpt
    else:
        title = latest.title
        body = latest.excerpt if latest.excerpt else latest.date

    notifier.send(title=title, body=body)
    print("Notificació enviada.")

    save_state({"last_hash": current_hash, "last_title": latest.title})


if __name__ == "__main__":
    main()
