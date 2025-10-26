import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

ENRICHED_PATH = Path("logs/enriched.jsonl")
ALERTS_LOG = Path("logs/alerts.log")

def load_enriched():
    if not ENRICHED_PATH.exists():
        return []
    out = []
    with ENRICHED_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out

def check_repeated_ips(window_minutes=10, threshold=3):
    records = load_enriched()
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    counts = defaultdict(int)
    events = defaultdict(list)

    for r in records:
        ts = r.get("timestamp") or r.get("parsed_at")
        try:
            # try parsing ISO-ish timestamps
            parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            # fallback: skip
            continue
        if parsed >= window_start:
            ip = r.get("ip") or r.get("enrichment", {}).get("ip")
            counts[ip] += 1
            events[ip].append(r)

    alerts = []
    for ip, cnt in counts.items():
        if ip and cnt >= threshold:
            alert = {
                "detected_at": now.isoformat() + "Z",
                "ip": ip,
                "count": cnt,
                "window_minutes": window_minutes,
                "sample_events": events[ip][:5],
            }
            alerts.append(alert)
            log_alert(alert)
    return alerts

def log_alert(alert: dict):
    ALERTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert) + "\n")
    print("[ALERT]", alert["ip"], "count:", alert["count"])

if __name__ == "__main__":
    a = check_repeated_ips() 
    print("Alerts:", a)
