# Unstuck Friday Rota (Streamlit + Slack)

A compact Streamlit app that builds a Friday rota from *today* to year-end, cycling through your team.

## Features
- Add/remove members and choose who starts
- Per-date overrides
- CSV export
- Slack notification test button
- Optional GitHub Actions for automatic Wednesday reminders

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Slack setup
Create an Incoming Webhook in Slack and paste the URL in the sidebar.
(Optional) Add Slack user IDs to mention users (e.g., U03ABCDEF).

## GitHub Actions (optional)
Set repo secret `SLACK_WEBHOOK_URL`. The workflow runs every Wednesday 07:00 UTC.
