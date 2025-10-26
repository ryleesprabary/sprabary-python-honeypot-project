from flask import Flask, jsonify, render_template_string
from collections import Counter
from pathlib import Path
import json

ENRICHED_PATH = Path("logs/enriched.jsonl")
app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<title>Local Dashboard</title>
<h1>Connection Dashboard</h1>
<p>Total attempts: {{ total }}</p>
<h2>Top 5 IPs</h2>
<ol>
{% for ip, count in top5 %}
  <li>{{ ip }} — {{ count }}</li>
{% endfor %}
</ol>
<h2>Credentials attempted (sample)</h2>
<ul>
{% for u in users %}
  <li>{{ u }}</li>
{% endfor %}
</ul>
<p><small>Data from logs/enriched.jsonl</small></p>
"""

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

@app.route("/api/stats")
def api_stats():
    records = load_enriched()
    total = len(records)
    ips = [r.get("ip") for r in records if r.get("ip")]
    users = [r.get("username") for r in records if r.get("username")]
    top5 = Counter(ips).most_common(5)
    unique_users = sorted(set(u for u in users if u))
    return jsonify({"total": total, "top5": top5, "users_sample": unique_users[:20]})

@app.route("/")
def index():
    stats = api_stats().get_json()
    return render_template_string(TEMPLATE, total=stats["total"], top5=stats["top5"], users=stats["users_sample"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
