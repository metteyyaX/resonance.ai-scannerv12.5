#!/usr/bin/env python3
# Resonance.ai v13.3 (Soliton) — WebSocket Breakout Scanner (no URL links in Discord alerts)

import os, json, time, uuid, csv, requests, threading
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    import websocket  # pip install websocket-client
except Exception:
    websocket = None

HERE = Path(__file__).resolve().parent

# -------------------- config loading --------------------
def load_envelope():
    p = HERE / "envelope.json"
    return json.loads(p.read_text())

ENV = load_envelope()

def jget(path, default=None):
    cur = ENV
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur

# -------------------- SCANNER knobs --------------------
UNIVERSE_FILE   = jget("SCANNER.UNIVERSE_PATH", "./data/universe/coinbase/universe.latest.jsonl")
REFRESH_SECONDS = float(jget("SCANNER.REFRESH_SECONDS", 1.0))

# Limits
CANDLE_INTERVAL = int(jget("SCANNER.LIMITS.CANDLE_INTERVAL_SECONDS", 60))
ABS_VOL_MIN_USD = float(jget("SCANNER.LIMITS.ABS_VOL_MIN_USD", 2000.0))

# Breakout window
SB               = jget("SCANNER.SINGLE_BAND", {}) or {}
SB_WIN           = int(SB.get("CANDLES", 10))
SB_PCT_OVER_HIGH = float(SB.get("BREAKOUT_THRESHOLD", 0.010))
SB_VOL_RATIO     = float(SB.get("VOLUME_SPIKE_RATIO", 1.30))

# Post-filters
PF                = jget("SCANNER.POST_FILTERS", {}) or {}
FILTERS_ENABLE    = bool(PF.get("ENABLED", True))
FILTER_LOGIC      = (PF.get("FILTER_LOGIC", "ALL") or "ALL").upper()

RSI_CFG           = PF.get("RSI", {}) or {}
RSI_ENABLE        = bool(RSI_CFG.get("ENABLED", True))
RSI_PRESET        = (RSI_CFG.get("PRESET", "DEFAULT") or "DEFAULT").upper()  # DEFAULT/SCALP/BALANCED/STRICT
RSI_PERIOD        = int(RSI_CFG.get("PERIOD", 14))
RSI_MIN           = float(RSI_CFG.get("LOW", 50))
RSI_MAX           = float(RSI_CFG.get("HIGH", 70))

VPM_CFG           = PF.get("VPM", {}) or {}
VPM_ENABLE        = bool(VPM_CFG.get("ENABLED", True))
VOLMIN_LOOK       = int(VPM_CFG.get("LOOKBACK_MIN", 5))
VOLMIN_FLOOR      = float(VPM_CFG.get("MIN_USD", 3000))

MACD_CFG          = PF.get("MACD", {}) or {}
MACD_ENABLE       = bool(MACD_CFG.get("ENABLED", True))
MACD_RULE         = (MACD_CFG.get("RULE", "hist_up") or "hist_up").lower()   # hist_up | line_cross | both
MACD_FAST         = int(MACD_CFG.get("FAST", 12))
MACD_SLOW         = int(MACD_CFG.get("SLOW", 26))
MACD_SIG          = int(MACD_CFG.get("SIGNAL", 9))

# Dedupe
DEDUP_SEC         = int(jget("SCANNER.DUPLICATE_CONTROL.MIN_SECONDS_BETWEEN_ALERTS_PER_PAIR", 90))

# Logging / Discord
LOG               = jget("SCANNER.LOGGING", {}) or {}
SAVE_DETECTIONS   = bool(LOG.get("SAVE_DETECTIONS", True))
CSV_PATH          = LOG.get("CSV_PATH", "./data/detections/detections.latest.csv")
JSONL_PATH        = LOG.get("JSONL_PATH", "./data/detections/detections.latest.jsonl")

DISCORD_WEBHOOK   = jget("SCANNER.DISCORD.WEBHOOK_DETECTIONS", "") or jget("discord.DISCORD_WEBHOOK_DETECTIONS", "")
HEALTH_WEBHOOK    = jget("SCANNER.DISCORD.WEBHOOK_HEALTH", "") or jget("discord.DISCORD_WEBHOOK_HEALTH", "")

def _norm_url(u: str | None) -> str | None:
    return u.replace("discordapp.com", "discord.com") if u else u
DISCORD_WEBHOOK = _norm_url(DISCORD_WEBHOOK)
HEALTH_WEBHOOK  = _norm_url(HEALTH_WEBHOOK)

# WebSocket
WS_ENABLED      = bool(jget("SCANNER.WS.ENABLED", False))
WS_URL          = jget("SCANNER.WS.URL", "wss://ws-feed.exchange.coinbase.com")
WS_CHANNEL      = (jget("SCANNER.WS.CHANNEL", "matches") or "matches").lower()  # matches|ticker
WS_EMIT         = (jget("SCANNER.WS.EMIT", "on_minute") or "on_minute").lower() # on_minute|on_trade
WS_RECONNECT    = int(jget("SCANNER.WS.RECONNECT_SECONDS", 5))
# NEW: Backfill config (from envelope.json)
BACKFILL_ENABLED = bool(jget("SCANNER.WS.BACKFILL.ENABLED", False))
BACKFILL_BARS    = int(jget("SCANNER.WS.BACKFILL.BARS", 0))  # number of 60s bars to seed
# (Your envelope shows BACKFILL enabled w/ BARS: 60.) 

# REST fallback
CB_REST = "https://api.exchange.coinbase.com"

# -------------------- utils --------------------
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def utc_hms(iso_utc: str) -> str:
    return iso_utc.split("T")[1].replace("Z","") if "T" in iso_utc else iso_utc
        
def _post_webhook(url, payload):
    # 5 tries; obey 429 retry_after
    for attempt in range(1, 6):
        try:
            r = requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"[discord] exception: {repr(e)}"); return False
        if 200 <= r.status_code < 300:
            print(f"[discord] -> {r.status_code}")
            return True
        if r.status_code == 429:
            wait = 1.0
            try: wait = float(r.json().get("retry_after", wait))
            except: wait = float(r.headers.get("Retry-After", wait) or 1.0)
            wait = max(0.0, wait)
            print(f"[discord] 429; retry_after={wait}s (attempt {attempt}/5)")
            time.sleep(wait)
            continue
        print(f"[discord] HTTP {r.status_code}: {r.text[:220]}")
        return False
    return False

def send_discord(msg: str):
    if not DISCORD_WEBHOOK:
        print("[discord] skipped: empty detections webhook"); 
        return
    ok = _post_webhook(DISCORD_WEBHOOK, {"content": msg})
    if not ok:
        clean = msg.replace("•","-").replace("×","x")
        if clean != msg:
            print("[discord] retrying with simplified content…")
            _post_webhook(DISCORD_WEBHOOK, {"content": clean})

def append_jsonl(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

_CSV_HEADER = ["t_detected","pair","price","interval","pct_over","vol_ratio","usd_per_min","rsi","vpm_avg_usd","macd_hist","source"]
def append_csv(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(_CSV_HEADER)
        filt = payload.get("filters", {})
        brk  = payload.get("breakout", {})
        w.writerow([
            payload.get("t_detected",""),
            payload.get("pair",""),
            f'{float(payload.get("price",0.0)):.8f}',
            payload.get("interval",""),
            f'{float(brk.get("pct_over",0.0))*100:.3f}',
            f'{float(brk.get("vol_ratio",0.0)):.3f}',
            f'{float(brk.get("usd_per_min",0.0)):.2f}',
            "" if filt.get("rsi") is None else f'{float(filt.get("rsi")):.1f}',
            "" if filt.get("vpm_avg_usd") is None else f'{float(filt.get("vpm_avg_usd")):.2f}',
            "" if filt.get("macd_hist") is None else f'{float(filt.get("macd_hist")):.6f}',
            payload.get("source","")
        ])

def load_pairs():
    p = HERE / UNIVERSE_FILE
    if not p.exists():
        return ["BTC-USD", "ETH-USD"]
    out = []
    with p.open() as f:
        for line in f:
            try:
                row = json.loads(line)
                pid = row.get("pair") or row.get("ex_symbol")
                if pid: out.append(pid)
            except:
                continue
    return out or ["BTC-USD","ETH-USD"]

def _universe_mtime():
    try:
        p = HERE / UNIVERSE_FILE
        return p.stat().st_mtime if p.exists() else None
    except Exception:
        return None

# -------------------- indicators --------------------
def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains  = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain*(period-1) + gains[i]) / period
        avg_loss = (avg_loss*(period-1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def ema(vals, period):
    k = 2/(period+1)
    e = [vals[0]]
    for v in vals[1:]:
        e.append((v - e[-1])*k + e[-1])
    return e

def compute_macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        return None
    e_fast = ema(closes, fast)
    e_slow = ema(closes, slow)
    macd_line = [f - s for f, s in zip(e_fast[-len(e_slow):], e_slow)]
    signal_line = ema(macd_line, signal)
    hist = macd_line[-1] - signal_line[-1]
    return {"macd": macd_line[-1], "signal": signal_line[-1], "hist": hist}

# -------------------- breakout & filters --------------------
def rsi_bounds_from_preset(default_low, default_high):
    p = RSI_PRESET
    if p in ("SCALP",): return 45, 72
    if p in ("BALANCED","DEFAULT"): return 50, 70
    if p in ("STRICT",): return 52, 68
    return default_low, default_high

def apply_filters(candles):
    if not FILTERS_ENABLE:
        return True, {}
    checks, details = [], {}
    closes = [c[4] for c in candles]

    # RSI
    rsi_low, rsi_high = rsi_bounds_from_preset(RSI_MIN, RSI_MAX)
    rsi_val = compute_rsi(closes, RSI_PERIOD) if RSI_ENABLE else None
    pass_rsi = True if not RSI_ENABLE else (True if rsi_val is None else (rsi_low <= rsi_val <= rsi_high))
    details["rsi"] = None if rsi_val is None else float(rsi_val)
    checks.append(pass_rsi)

    # VPM (avg USD/min over lookback, excluding current)
    if VPM_ENABLE and len(candles) >= max(VOLMIN_LOOK, 2):
        usd_vals = [c[5]*c[4] for c in candles[-VOLMIN_LOOK:]]
        prev = usd_vals[:-1] if len(usd_vals) > 1 else usd_vals
        avg_usd = sum(prev)/max(len(prev),1)
        pass_vpm = (avg_usd >= VOLMIN_FLOOR)
        details["vpm_avg_usd"] = float(avg_usd)
        checks.append(pass_vpm)
    else:
        checks.append(True)

    # MACD
    macdinfo = compute_macd(closes, MACD_FAST, MACD_SLOW, MACD_SIG) if MACD_ENABLE else None
    if MACD_ENABLE and macdinfo is not None:
        details["macd_hist"] = float(macdinfo["hist"])
        if   MACD_RULE == "hist_up":    pass_macd = macdinfo["hist"] > 0
        elif MACD_RULE == "line_cross": pass_macd = macdinfo["macd"] > macdinfo["signal"]
        else:                           pass_macd = macdinfo["hist"] > 0 and macdinfo["macd"] > macdinfo["signal"]
    else:
        pass_macd = True
        details["macd_hist"] = None
    checks.append(pass_macd)

    ok = (all(checks) if FILTER_LOGIC == "ALL" else any(checks))
    return ok, details

def is_breakout_window(cset, pct_over_high, vol_ratio_required, abs_usd_floor):
    if len(cset) < 3: return False, {}
    highs = [c[2] for c in cset]
    closes= [c[4] for c in cset]
    vols  = [c[5] for c in cset]
    max_high = max(highs[:-1])
    last_close = closes[-1]
    prev_avg_vol = sum(vols[:-1]) / max(len(vols[:-1]), 1)
    last_vol = vols[-1]
    usd = last_vol * last_close
    pct_over = (last_close/max_high - 1.0) if max_high > 0 else 0.0
    vol_ratio = (last_vol/prev_avg_vol) if prev_avg_vol > 0 else 0.0
    hit = (last_close > max_high * (1.0 + pct_over_high) and
           vol_ratio >= vol_ratio_required and
           usd >= abs_usd_floor)
    info = {"last": last_close, "max_high": max_high, "pct_over": pct_over,
            "vol_ratio": vol_ratio, "usd_per_min": usd}
    return hit, info

# -------------------- WS aggregation --------------------
class CandleAgg:
    def __init__(self, interval=60, lookback=max(120, SB_WIN+10)):
        self.intv = interval
        self.look = lookback
        self.cur  = {}
        self.hist = {}
        self.lock = threading.Lock()

    def _bucket(self, tsec): return int(tsec - (tsec % self.intv))

    def on_trade(self, pid, price, size, tsec):
        b = self._bucket(tsec)
        with self.lock:
            cd = self.cur.get(pid)
            if not cd or cd["b"] != b:
                if cd: self._finalize(pid, cd)
                self.cur[pid] = {"b": b, "o": price, "h": price, "l": price, "c": price, "v": size}
            else:
                cd["c"] = price
                if price > cd["h"]: cd["h"] = price
                if price < cd["l"]: cd["l"] = price
                cd["v"] += size

    def _finalize(self, pid, cd):
        arr = [cd["b"], cd["o"], cd["h"], cd["l"], cd["c"], cd["v"]]
        h = self.hist.setdefault(pid, [])
        h.append(arr)
        if len(h) > self.look:
            del h[:len(h) - self.look]

    def flush_if_due(self, now_ts):
        with self.lock:
            for pid, cd in list(self.cur.items()):
                if cd and now_ts - cd["b"] >= self.intv:
                    self._finalize(pid, cd)
                    self.cur[pid] = None

    def candles(self, pid):
        with self.lock:
            return list(self.hist.get(pid, []))

# -------------------- WebSocket client --------------------
class CBWebSocket(threading.Thread):
    def __init__(self, url, pairs, channel="matches", on_trade=None):
        super().__init__(daemon=True)
        self.url = url; self.pairs = pairs; self.channel = channel
        self.on_trade = on_trade
        self.stop_flag = threading.Event()
        self.ws = None

    def run(self):
        while not self.stop_flag.is_set():
            try: self._loop()
            except Exception as e: print("[ws] error:", e)
            time.sleep(max(WS_RECONNECT, 2))

    def _loop(self):
        if websocket is None:
            print("✗ websocket-client not installed. Run: pip install websocket-client")
            self.stop_flag.set(); return

        def on_open(ws):
            sub = {"type": "subscribe", "channels": [{"name": self.channel, "product_ids": self.pairs}]}
            ws.send(json.dumps(sub))
            print(f"[ws] subscribed to {self.channel} for {len(self.pairs)} products")

        def on_message(ws, message):
            try: m = json.loads(message)
            except Exception: return
            t = m.get("type"); pid = m.get("product_id")
            if not pid: return
            if self.channel == "matches" and t in ("match", "last_match"):
                price = float(m.get("price") or 0.0); size = float(m.get("size") or 0.0); ts = m.get("time")
            elif self.channel == "ticker" and t == "ticker":
                price = float(m.get("price") or 0.0); size = float(m.get("last_size") or 0.0); ts = m.get("time")
            else: return
            if not price: return
            try: tsec = datetime.fromisoformat((ts or "").replace("Z","+00:00")).timestamp()
            except Exception: tsec = time.time()
            if self.on_trade: self.on_trade(pid, price, size, tsec)

        def on_error(ws, err): print("[ws] socket error:", err)
        def on_close(ws, code, msg): print(f"[ws] closed ({code}) {msg}")

        self.ws = websocket.WebSocketApp(self.url,
            on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        self.ws.run_forever(ping_interval=20, ping_timeout=10)

    def stop(self):
        self.stop_flag.set()
        try:
            if self.ws: self.ws.close()
        except Exception:
            pass

# -------------------- REST helpers --------------------
def get_candles_rest(product_id, granularity=CANDLE_INTERVAL):
    try:
        end = datetime.now(timezone.utc)
        # Pull enough bars to cover SB_WIN and backfill request
        need = max(SB_WIN + 5, BACKFILL_BARS, 60)
        start = end - timedelta(seconds=granularity * need)
        url = f"{CB_REST}/products/{product_id}/candles"
        params = {
            "granularity": granularity,
            "start": start.isoformat().replace("+00:00","Z"),
            "end": end.isoformat().replace("+00:00","Z"),
        }
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        if not isinstance(data, list): return []
        data.sort(key=lambda c: c[0])  # oldest->newest
        return data
    except Exception as e:
        print("REST error", e)
        return []

def seed_from_rest(agg, pairs, bars):
    """Seed CandleAgg history from REST so WS detections/filters can run immediately."""
    bars = max(0, int(bars))
    if bars <= 0: 
        return
    for pid in pairs:
        data = get_candles_rest(pid, granularity=CANDLE_INTERVAL)  # [time, low, high, open, close, volume]
        if not data:
            continue
        # map CB order -> our CandleAgg hist order: [b, o, h, l, c, v]
        mapped = [[t, o, h, l, c, v] for (t, l, h, o, c, v) in data]
        # keep last N, bounded by agg.look
        hist = mapped[-min(bars, agg.look):]
        agg.hist[pid] = hist

# -------------------- dedupe --------------------
_last_alert_ts = {}
def is_duplicate(pair: str, min_seconds: int) -> bool:
    now = time.time()
    last = _last_alert_ts.get(pair, 0.0)
    if now - last < min_seconds: return True
    _last_alert_ts[pair] = now; return False

# -------------------- detection & emit --------------------
def try_detect(pair: str, candles: list):
    win = max(SB_WIN, 3)
    window = candles[-win:]
    hit, info = is_breakout_window(window, SB_PCT_OVER_HIGH, SB_VOL_RATIO, ABS_VOL_MIN_USD)
    if not hit: return

    ok, filt = apply_filters(candles)
    if not ok: return
    if is_duplicate(pair, DEDUP_SEC): return

    price = float(candles[-1][4])
    det = {
        "schema": "resonance_alert_v3",
        "id": str(uuid.uuid4()),
        "pair": pair,
        "t_detected": now_iso(),
        "price": price,
        "interval": f"{CANDLE_INTERVAL}s",
        "filters": {
            "rsi": filt.get("rsi"),
            "vpm_avg_usd": filt.get("vpm_avg_usd"),
            "macd_hist": filt.get("macd_hist")
        },
        "breakout": {
            "pct_over": info["pct_over"],
            "vol_ratio": info["vol_ratio"],
            "usd_per_min": info["usd_per_min"],
            "max_high": info["max_high"]
        },
        "source": "resonance_scanner_v13.3_ws",
        "universe": "coinbase"
    }

    print("SELECTED", det)
    if SAVE_DETECTIONS:
        append_jsonl(HERE/JSONL_PATH, det)
        append_csv(HERE/CSV_PATH, det)

        # ---- Discord message ----
    utc_txt = utc_hms(det["t_detected"])
    msg = (
        "🚀 Breakout: {pair}\n"
        "UTC: {utc}\n"
        "Price: {price:.6f} ({interval})\n"
        "Breakout Δ%: {pct:.2f}% • V/avg: {vr:.2f}× • USD/min: {usd:,.0f}\n"
        "RSI: {rsi} • MACD hist: {hist}\n"
        "v13.4 • soliton"
    ).format(
        pair=pair,
        utc=utc_txt,
        price=price,
        interval=det["interval"],
        pct=det["breakout"]["pct_over"]*100,
        vr=det["breakout"]["vol_ratio"],
        usd=det["breakout"]["usd_per_min"],
        rsi=("n/a" if det["filters"]["rsi"] is None else f'{float(det["filters"]["rsi"]):.1f}'),
        hist=("n/a" if det["filters"]["macd_hist"] is None else f'{float(det["filters"]["macd_hist"]):.5f}')
    )

    send_discord(msg)

# -------------------- main --------------------
def main():
    pairs = load_pairs()
    uni_mtime = _universe_mtime()
    print(f"--- Resonance WS Scanner — pairs={len(pairs)} — WS={'on' if WS_ENABLED else 'off'} ---")
    print("[scanner] detections webhook:", ("set" if DISCORD_WEBHOOK else "MISSING"))
    if HEALTH_WEBHOOK:
        print("[scanner] health webhook: set")
    send_discord(f"🟢 Scanner online (v13.3 • soliton) {now_iso()} — pairs={len(pairs)}")

    if WS_ENABLED:
        def start_ws(pairs, agg):
            def _on_trade(pid, price, size, tsec):
                agg.on_trade(pid, price, size, tsec)
                if WS_EMIT == "on_trade":
                    cs = agg.candles(pid)
                    if len(cs) >= SB_WIN:
                        try_detect(pid, cs)
            ws_thr = CBWebSocket(WS_URL, pairs, channel=WS_CHANNEL, on_trade=_on_trade)
            ws_thr.start(); return ws_thr

        agg = CandleAgg(interval=CANDLE_INTERVAL, lookback=max(120, SB_WIN+20))

        # NEW: REST backfill (warm start) before opening WS
        if BACKFILL_ENABLED and BACKFILL_BARS > 0:
            print(f"[backfill] Seeding last {BACKFILL_BARS} bars via REST for {len(pairs)} pairs…", flush=True)
            seed_from_rest(agg, pairs, BACKFILL_BARS)

        ws_thread = start_ws(pairs, agg)

        try:
            while True:
                # hot reload
                cur_mtime = _universe_mtime()
                if cur_mtime and cur_mtime != uni_mtime:
                    new_pairs = load_pairs()
                    if set(new_pairs) != set(pairs):
                        print(f"[universe] change detected → reloading pairs {len(pairs)} → {len(new_pairs)}")
                        try: ws_thread.stop(); time.sleep(0.2)
                        except Exception: pass
                        agg = CandleAgg(interval=CANDLE_INTERVAL, lookback=max(120, SB_WIN+20))
                        if BACKFILL_ENABLED and BACKFILL_BARS > 0:
                            print(f"[backfill] Seeding last {BACKFILL_BARS} bars via REST after universe change…", flush=True)
                            seed_from_rest(agg, new_pairs, BACKFILL_BARS)
                        ws_thread = start_ws(new_pairs, agg)
                        pairs = new_pairs
                    uni_mtime = cur_mtime

                # emit cycle
                agg.flush_if_due(time.time())
                if WS_EMIT == "on_minute":
                    for pid in pairs:
                        cs = agg.candles(pid)
                        if len(cs) >= SB_WIN:
                            try_detect(pid, cs)

                print(f"[heartbeat/ws] {now_iso()} pairs={len(pairs)}", flush=True)
                time.sleep(max(0.5, REFRESH_SECONDS))
        except KeyboardInterrupt:
            pass
        finally:
            ws_thread.stop()

    else:
        try:
            while True:
                cur_mtime = _universe_mtime()
                if cur_mtime and cur_mtime != uni_mtime:
                    new_pairs = load_pairs()
                    if set(new_pairs) != set(pairs):
                        print(f"[universe] (REST) change detected → {len(pairs)} → {len(new_pairs)}")
                        pairs = new_pairs
                    uni_mtime = cur_mtime

                print(f"[heartbeat/rest] {now_iso()} scanning {UNIVERSE_FILE} (pairs={len(pairs)})", flush=True)
                for pid in pairs:
                    cs = get_candles_rest(pid)
                    if len(cs) >= SB_WIN:
                        try_detect(pid, cs)
                time.sleep(max(1.0, REFRESH_SECONDS))
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
