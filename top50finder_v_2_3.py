#!/usr/bin/env python3
# Top50 (Coinbase) v2.2 — unified envelope + live progress counter

import os, json, time, tempfile, requests, sys
from pathlib import Path
from datetime import datetime, timezone
from math import isfinite

def _bool(x: str) -> bool:
    return str(x).strip().lower() in ("1","true","yes","on")

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def read_env(base: Path) -> dict:
    env = {}
    p = base / ".env"
    if p.exists():
        for raw in p.read_text().splitlines():
            s = raw.strip()
            if not s or s.startswith("#") or "=" not in s: continue
            k, v = s.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def read_envelope(base: Path) -> dict:
    p = base / "envelope.json"
    if not p.exists():
        raise FileNotFoundError("envelope.json not found next to Top50 script")
    return json.loads(p.read_text())

def write_jsonl_atomic(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", text=True)
    with os.fdopen(fd, "w") as f:
        for r in rows:
            if "ts" not in r:
                r["ts"] = now_utc_iso()
            f.write(json.dumps(r) + "\n")
    os.replace(tmp, path)

def send_discord(webhook: str | None, msg: str):
    if not webhook: return
    try:
        requests.post(webhook, json={"content": msg}, timeout=6)
    except Exception as e:
        print(f"[warn] discord health ping failed: {e}", flush=True)

def msleep(ms: int):
    time.sleep(max(ms, 0) / 1000.0)

# ---------- Coinbase public endpoints ----------
CB_BASE = "https://api.exchange.coinbase.com"

def cb_get_products() -> list[dict]:
    r = requests.get(f"{CB_BASE}/products", timeout=10)
    r.raise_for_status()
    return r.json()

def cb_get_stats(product_id: str) -> dict:
    r = requests.get(f"{CB_BASE}/products/{product_id}/stats", timeout=10)
    r.raise_for_status()
    return r.json()

def cb_get_ticker(product_id: str) -> dict:
    r = requests.get(f"{CB_BASE}/products/{product_id}/ticker", timeout=10)
    r.raise_for_status()
    return r.json()

# ---------- core selection logic ----------
def build_universe(base: Path) -> dict:
    env = read_env(base)
    j = read_envelope(base)

    # ops controls
    throttle_ms = int(env.get("REST_THROTTLE_MS", j.get("ops", {}).get("REST_THROTTLE_MS", 80)))
    webhook = (j.get("discord", {}) or {}).get("DISCORD_WEBHOOK_HEALTH") or env.get("DISCORD_HEALTH_WEBHOOK", "").strip() or None
    out_path = Path(env.get("UNIVERSE_FILE", j.get("ops", {}).get("UNIVERSE_FILE", "data/universe/coinbase/universe.latest.jsonl")))

    # strategy knobs
    uni = j.get("universe", {})
    QUOTE = uni.get("quote_asset", "USD")
    MAX_PAIRS = int(uni.get("max_pairs", 50))
    MAX_SPREAD = float(uni.get("max_spread", 0.005))          # e.g. 0.005 = 0.5%
    MIN_QVOL = float(uni.get("min_24h_vol_quote", 3_000_000)) # in quote units ($ if USD)

    print(f"[Top50] Fetching product list from {CB_BASE} …", flush=True)
    products = cb_get_products()
    print(f"[Top50] Received {len(products)} products. Filtering for {QUOTE} spot…", flush=True)

    # keep only active, USD-quoted spot trading markets
    candidates = []
    for p in products:
        if p.get("quote_currency") != QUOTE: continue
        if p.get("status") != "online": continue
        if p.get("trading_disabled"): continue
        candidates.append(p["id"])

    total = len(candidates)
    print(f"[Top50] {total} candidates. Scoring with spread ≤ {MAX_SPREAD*100:.2f}% and 24h quote vol ≥ ${MIN_QVOL:,.0f} …", flush=True)

    # 2) pull stats + ticker, compute metrics
    scored = []
    for i, pid in enumerate(candidates, start=1):
        print(f"[Top50] Processing {i}/{total}: {pid}", flush=True)   # Live progress
        try:
            stats = cb_get_stats(pid)
            ticker = cb_get_ticker(pid)
        except Exception as e:
            print(f"[skip] {pid}: fetch error {e}", flush=True)
            msleep(throttle_ms)
            continue

        # bid/ask and price for quote volume approximation
        try:
            bid = float(ticker.get("bid") or 0.0)
            ask = float(ticker.get("ask") or 0.0)
        except ValueError:
            bid = ask = 0.0

        # spread
        spread = None
        if ask and bid and ask > 0:
            spread = (ask - bid) / ask

        # 24h base volume *approx* to quote using mid price
        try:
            base_vol_24h = float(stats.get("volume") or 0.0)  # base units
        except ValueError:
            base_vol_24h = 0.0
        mid = (ask + bid) / 2.0 if ask and bid else float(stats.get("last") or 0.0) or 0.0
        quote_vol_24h = base_vol_24h * mid if (base_vol_24h and mid) else 0.0

        # filter guards
        if spread is None or not isfinite(spread): 
            msleep(throttle_ms); 
            continue
        if spread > MAX_SPREAD:
            msleep(throttle_ms)
            continue
        if quote_vol_24h < MIN_QVOL:
            msleep(throttle_ms)
            continue

        scored.append({
            "pair": pid,              # common name in your stack
            "ex_symbol": pid,         # same for coinbase
            "spread": round(spread, 6),
            "vol24h_quote": round(quote_vol_24h, 2),
        })
        msleep(throttle_ms)

    # 3) rank: lowest spread, highest quote vol
    scored.sort(key=lambda r: (r["spread"], -r["vol24h_quote"]))
    selected = scored[:MAX_PAIRS]

    # 4) write JSONL atomically
    write_jsonl_atomic(out_path, selected)

    # 5) discord health ping
    msg = (
        "✅ **Top50 refresh OK**\n"
        f"Pairs: **{len(selected)}** of {len(candidates)} candidates\n"
        f"Filters: spread ≤ {MAX_SPREAD*100:.2f}% | 24h quote vol ≥ ${MIN_QVOL:,.0f}\n"
        f"Quote: {QUOTE} | File: `{out_path}` | Time: {now_utc_iso()}"
    )
    send_discord(webhook, msg)

    return {
        "selected": len(selected),
        "candidates": len(candidates),
        "out_file": str(out_path),
        "filters": {"max_spread": MAX_SPREAD, "min_24h_vol_quote": MIN_QVOL, "quote": QUOTE}
    }

def main():
    base = Path(__file__).resolve().parent
    print(f"[Top50] Starting in {base}", flush=True)
    try:
        j = read_envelope(base)
        print(f"[Top50] Loaded envelope.json keys: {list(j.keys())}", flush=True)
        print(f"[Top50] Universe file target: {j.get('ops', {}).get('UNIVERSE_FILE', './data/universe/coinbase/universe.latest.jsonl')}", flush=True)
    except Exception as e:
        print(f"[Top50][ERROR] {e}", flush=True)
        sys.exit(1)

    env = read_env(base)
    run_once = _bool(env.get("RUN_ONCE", str(j.get('ops', {}).get('RUN_ONCE', True))))
    interval_min = int(env.get("REFRESH_INTERVAL_MINUTES", j.get("ops", {}).get("REFRESH_INTERVAL_MINUTES", 20)))

    while True:
        try:
            info = build_universe(base)
            print(f"[Top50] wrote {info['selected']} pairs to {info['out_file']} @ {now_utc_iso()}", flush=True)
        except Exception as e:
            j2 = {}
            try:
                j2 = read_envelope(base)
            except Exception:
                pass
            webhook = (j2.get("discord", {}) or {}).get("DISCORD_WEBHOOK_HEALTH") or env.get("DISCORD_HEALTH_WEBHOOK", "").strip() or None
            send_discord(webhook, f"❌ **Top50 refresh FAILED** @ {now_utc_iso()}\nError: `{e}`")
            print(f"[Top50][ERROR] {e}", flush=True)

        if run_once:
            break
        time.sleep(max(60, interval_min * 60))

if __name__ == "__main__":
    main()
