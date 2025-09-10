# serve_detections.py  (Flask version)
import os, json
from pathlib import Path
from flask import Flask, send_file, Response, render_template_string
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ENV = json.loads((HERE / "envelope.json").read_text())

def _abs(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else (HERE / q).resolve()

LOG = (ENV.get("SCANNER", {}) or {}).get("LOGGING", {}) or {}
CSV = _abs(LOG.get("CSV_PATH", "./data/detections/detections.latest.csv"))
JSONL = _abs(LOG.get("JSONL_PATH", "./data/detections/detections.latest.jsonl"))

app = Flask(__name__)

@app.get("/")
def index():
    t = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html = f"""
    <h2>Resonance.ai – File Export</h2>
    <p>Server time: {t}</p>
    <ul>
      <li><a href="/detections.jsonl">detections.jsonl</a> — {{'ok' if JSONL.exists() else 'not found'}}</li>
      <li><a href="/detections.csv">detections.csv</a> — {{'ok' if CSV.exists() else 'not found'}}</li>
    </ul>"""
    return render_template_string(html, CSV=CSV, JSONL=JSONL)

@app.get("/detections.csv")
def get_csv():
    if not CSV.exists(): return Response("not found", 404)
    return send_file(str(CSV), mimetype="text/csv", as_attachment=False)

@app.get("/detections.jsonl")
def get_jsonl():
    if not JSONL.exists(): return Response("not found", 404)
    return send_file(str(JSONL), mimetype="application/json", as_attachment=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","8080")), debug=False)