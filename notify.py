import sys, requests
from datetime import date
from typing import Dict

from rota_core import load_config, next_upcoming_friday, get_fridays, build_rotation, apply_overrides

def slack_format_name(name: str, id_map: Dict[str, str]) -> str:
    uid = (id_map or {}).get(name)
    return f"<@{uid}>" if uid else name

def build_message(assignee: str, friday_iso: str, id_map: Dict[str, str]) -> str:
    target = slack_format_name(assignee, id_map)
    return (f"Heads up {target}! You’re on *Friday lead-check rota* for *{friday_iso}*\n"
            f"Please confirm you’ve scheduled your checks. Thanks!")

def send_slack_message(webhook_url: str, text: str):
    resp = requests.post(webhook_url, json={"text": text}, timeout=10)
    if resp.status_code >= 300:
        raise RuntimeError(f"Slack webhook error: {resp.status_code} {resp.text}")

def main():
    cfg = load_config()
    if not cfg.slack_webhook_url:
        print("No SLACK webhook configured. Skipping.")
        return 0

    today = date.today()
    year_end = date(today.year, 12, 31)
    fridays = get_fridays(today, year_end)
    base = build_rotation(fridays, cfg.members, cfg.start_member)
    final = apply_overrides(base, cfg.overrides)

    upcoming = next_upcoming_friday(today)
    if not upcoming:
        print("No upcoming Fridays in current year.")
        return 0

    key = upcoming.isoformat()
    assignee = final.get(key)
    if not assignee:
        print(f"No assignee for {key}.")
        return 0

    text = build_message(assignee, key, cfg.slack_id_map)
    send_slack_message(cfg.slack_webhook_url, text)
    print(f"Sent Slack notification for {key} to {assignee}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
