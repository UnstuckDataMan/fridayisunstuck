from datetime import date
import pandas as pd
import streamlit as st

from rota_core import (
    load_config, save_config, get_fridays, build_rotation,
    apply_overrides, next_upcoming_friday, RotaConfig
)
from notify import build_message, send_slack_message

st.set_page_config(page_title="Unstuck Friday Rota", page_icon="📅", layout="centered")
st.title("📅 Unstuck Friday Rota")

cfg = load_config()

with st.sidebar:
    st.header("Settings")

    st.subheader("Team members (rotation order)")
    members_text = st.text_area("One name per line", value="\n".join(cfg.members), height=120)
    members = [m.strip() for m in members_text.splitlines() if m.strip()]

    start_member = st.selectbox("Start with", options=members or [cfg.start_member],
                                index=(members or cfg.members).index(cfg.start_member) if (members and cfg.start_member in members) else 0)

    st.markdown("---")
    st.subheader("Slack")
    slack_webhook_url = st.text_input("Incoming Webhook URL", value=cfg.slack_webhook_url, type="password")

    st.caption("Optional: map names to Slack IDs for @mentions (format: name, UXXXX …)")
    map_rows = []
    keys = sorted(set(list((cfg.slack_id_map or {}).keys()) + members))
    for k in keys:
        map_rows.append({"name": k, "slack_id": (cfg.slack_id_map or {}).get(k, "")})
    map_df = pd.DataFrame(map_rows)
    edited_map = st.data_editor(map_df, num_rows="dynamic", use_container_width=True, key="id_map")
    new_id_map = {row["name"]: row["slack_id"] for _, row in edited_map.iterrows() if row.get("name")}

    st.markdown("---")
    if st.button("💾 Save settings"):
        cfg.members = members or cfg.members
        cfg.start_member = start_member
        cfg.slack_webhook_url = slack_webhook_url
        cfg.slack_id_map = new_id_map
        save_config(cfg)
        st.success("Settings saved.")

today = date.today()
year_end = date(today.year, 12, 31)
fridays = get_fridays(today, year_end)
base_sched = build_rotation(fridays, members or cfg.members, start_member)

st.subheader("Schedule")
ov_rows = []
for d_iso, who in base_sched.items():
    ov_val = (cfg.overrides or {}).get(d_iso, "")
    ov_rows.append({"date": d_iso, "assignee": who, "override": ov_val})

ov_df = pd.DataFrame(ov_rows)
edited = st.data_editor(
    ov_df,
    column_config={
        "date": st.column_config.TextColumn(disabled=True),
        "assignee": st.column_config.TextColumn(disabled=True),
        "override": st.column_config.TextColumn(help="Leave blank to keep rotation")
    },
    use_container_width=True,
)

new_overrides = {row["date"]: str(row["override"]).strip() for _, row in edited.iterrows() if str(row.get("override", "")).strip()}
final_sched = apply_overrides(base_sched, new_overrides or (cfg.overrides or {}))

final_rows = [{"date": k, "on_duty": v} for k, v in final_sched.items()]
final_df = pd.DataFrame(final_rows)
st.dataframe(final_df, use_container_width=True)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("✅ Save overrides"):
        cfg.overrides = new_overrides
        save_config(cfg)
        st.success("Overrides saved.")
with c2:
    csv = final_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export CSV", data=csv, file_name="friday_rota.csv", mime="text/csv")
with c3:
    if st.button("🔔 Send test Slack (next Friday)"):
        if not (cfg.slack_webhook_url or slack_webhook_url):
            st.error("No Slack webhook configured in Settings.")
        else:
            upcoming = next_upcoming_friday(today)
            if not upcoming:
                st.warning("No upcoming Friday this year.")
            else:
                key = upcoming.isoformat()
                who = final_sched.get(key)
                msg = build_message(who, key, new_id_map or (cfg.slack_id_map or {}))
                try:
                    send_slack_message(slack_webhook_url or cfg.slack_webhook_url, msg)
                    st.success(f"Sent Slack notification for {key} to {who}.")
                except Exception as e:
                    st.error(f"Failed to send Slack message: {e}")

st.info("Tip: Use the included GitHub Action to automate Wednesday reminders.")
