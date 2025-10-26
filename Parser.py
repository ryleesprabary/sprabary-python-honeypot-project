# parser.py
# Author: Rylee Sprabary
# Purpose: Read JSONL honeypot logs, extract unique IPs/usernames, add mock GeoIP tags,
#          and write enriched results to logs/enriched.jsonl.
# Notes:   Works offline (no internet). Safe for host-only networks.

from pathlib import Path
import json
import ipaddress
from datetime import datetime, timezone
import schedule, time
import sys

BASE = Path(__file__).resolve().parents[1]          # .../honeypot
INFILE = BASE / "logs" / "connections.jsonl"
OUTFILE = BASE / "logs" / "enriched.jsonl"

def is_private(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False

def geoip_mock(ip: str) -> dict:
    """Offline enrichment: classify private vs internet; add simple tags."""
    if ip in ("127.0.0.1", "::1"):
        return {"scope":"loopback","country":"LOCAL","asn":"LOOPBACK","org":"Localhost","tags":["loopback"]}
    if is_private(ip):
        return {"scope":"private","country":"LAN","asn":"RFC1918","org":"Private Address Space","tags":["internal","rfc1918"]}
    return {"scope":"internet","country":"UNK","asn":"UNK","org":"Unknown","tags":["internet"]}

def parse_lines() -> list:
    """Read connections.jsonl and return enriched unique events."""
    if not INFILE.exists():
        return []

    seen = set()  # de-dup by (ip, timestamp, banner)
    enriched = []

    with INFILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue

            ip = evt.get("client_ip") or evt.get("ip") or "0.0.0.0"
            ts = evt.get("timestamp") or evt.get("ts") or datetime.now(timezone.utc).isoformat()
            banner = evt.get("banner_sent") or evt.get("banner") or ""
            username = evt.get("username") or None  # will be None unless you add auth capture later

            key = (ip, ts, banner)
            if key in seen:
                continue
            seen.add(key)

            geo = geoip_mock(ip)

            out = {
                "client_ip": ip,
                "timestamp": ts,
                "username": username,
                "banner": banner,
                "geo_scope": geo["scope"],
                "geo_country": geo["country"],
                "asn": geo["asn"],
                "org": geo["org"],
                "tags": geo["tags"],
            }
            enriched.append(out)

    return enriched

def write_enriched(rows: list) -> None:
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def run_parser():
    rows = parse_lines()
    write_enriched(rows)
    print(f"[parser] wrote {len(rows)} rows -> {OUTFILE}")

def main():
    # demo: --once runs immediately and exits; default = scheduled every 10 minutes
    if "--once" in sys.argv:
        run_parser()
        return
    schedule.every(10).minutes.do(run_parser)
    print("[parser] scheduling every 10 minutes; Ctrl+C to stop")
    run_parser()  # do one run at start
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
