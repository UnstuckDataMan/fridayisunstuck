import json
import os
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

CONFIG_PATH = os.path.join("data", "rota_config.json")
DEFAULT_MEMBERS = ["Chris", "Dylan", "Elizma", "Leo", "Oliver"]

@dataclass
class RotaConfig:
    members: List[str]
    start_member: str
    slack_webhook_url: str = ""
    slack_id_map: Dict[str, str] = None
    overrides: Dict[str, str] = None

    def to_json(self):
        d = asdict(self)
        if d.get("slack_id_map") is None:
            d["slack_id_map"] = {}
        if d.get("overrides") is None:
            d["overrides"] = {}
        return d

def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def load_config() -> "RotaConfig":
    ensure_data_dir()
    if not os.path.exists(CONFIG_PATH):
        cfg = RotaConfig(
            members=DEFAULT_MEMBERS.copy(),
            start_member=DEFAULT_MEMBERS[0],
            slack_webhook_url="",
            slack_id_map={},
            overrides={},
        )
        save_config(cfg)
        return cfg
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return RotaConfig(
        members=raw.get("members", DEFAULT_MEMBERS.copy()),
        start_member=raw.get("start_member", DEFAULT_MEMBERS[0]),
        slack_webhook_url=raw.get("slack_webhook_url", ""),
        slack_id_map=raw.get("slack_id_map", {}) or {},
        overrides=raw.get("overrides", {}) or {},
    )

def save_config(cfg: "RotaConfig"):
    ensure_data_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg.to_json(), f, indent=2)

def first_friday_on_or_after(d: date) -> date:
    days_ahead = (4 - d.weekday()) % 7  # Friday=4
    return d + timedelta(days=days_ahead)

def get_fridays(from_date: date, to_date: date):
    fr = first_friday_on_or_after(from_date)
    out = []
    while fr <= to_date:
        out.append(fr)
        fr += timedelta(days=7)
    return out

def build_rotation(fridays, members, start_member):
    if not members:
        return {}
    start_idx = members.index(start_member) if start_member in members else 0
    sched = {}
    idx = start_idx
    for fr in fridays:
        sched[fr.isoformat()] = members[idx % len(members)]
        idx += 1
    return sched

def apply_overrides(schedule, overrides):
    out = schedule.copy()
    for k, v in (overrides or {}).items():
        if k in out and v:
            out[k] = v
    return out

def next_upcoming_friday(today: Optional[date] = None) -> Optional[date]:
    today = today or date.today()
    this_year_end = date(today.year, 12, 31)
    fridays = get_fridays(today, this_year_end)
    return fridays[0] if fridays else None
