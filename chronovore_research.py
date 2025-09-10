#!/usr/bin/env python3
"""
Chronovore Research Bot — Coinbase
- Reads ./data/detections/detections.latest.jsonl and simulates trades
- Envelope.json integration (RESEARCH.* block)
- Always returns win|loss|timeout (no 'bad-data')
- Progress prints while processing
"""

import datetime as dt
import json, os, time, gzip
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import requests

DEFAULT_FILE = "./data/detections/detections.latest.jsonl"

# ----------------------------- Config -----------------------------
@dataclass
class Config:
    detections_path: str = DEFAULT_FILE
    lookback_days: int = 14

    tp_pct: float = 3.0          # percent
    sl_pct: float = 1.0          # percent
    fee_bps: float = 5.0         # round-trip fee, in bps (e.g., 236 = 2.36%)
    slip_bps: float = 0.0        # entry slippage, in bps
    max_hold_min: int = 180
    first_touch_mode: str = "conservative_stop_first"  # or "optimistic_target_first"

    # 1-minute candles
    granularity_sec: int = 60

    # I/O + network
    out_dir: str = "./data/research"
    coinbase_endpoint: str = "https://api.exchange.coinbase.com"
    fetch_retries: int = 2
    fetch_retry_wait_sec: int = 2
    fresh_skip_min: int = 5
    missing_data_policy: str = "loss"   # loss | timeout | skip

    # Indicators (snapshotted at detection)
    vol_ma_window: int = 20
    overhigh_lookback_min: int = 60
    rsi_len: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9


# ----------------------------- Envelope -----------------------------
def _load_envelope_for_research() -> Dict[str, Any]:
    try:
        here = Path(__file__).resolve().parent
        p = here / "envelope.json"
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return {}

def _apply_envelope_overrides(cfg: Config) -> Config:
    env = _load_envelope_for_research()
    if not env:
        return cfg
    r = (env.get("RESEARCH") or {})

    cfg.detections_path   = r.get("DETECTIONS_PATH", cfg.detections_path)
    cfg.out_dir           = r.get("OUT_DIR", cfg.out_dir)

    cfg.lookback_days     = int(r.get("LOOKBACK_DAYS", cfg.lookback_days))
    cfg.tp_pct            = float(r.get("TP_PCT", cfg.tp_pct))
    cfg.sl_pct            = float(r.get("SL_PCT", cfg.sl_pct))
    cfg.fee_bps           = float(r.get("FEE_BPS", cfg.fee_bps))
    cfg.slip_bps          = float(r.get("SLIP_BPS", cfg.slip_bps))
    cfg.max_hold_min      = int(r.get("MAX_HOLD_MIN", cfg.max_hold_min))
    cfg.first_touch_mode  = str(r.get("FIRST_TOUCH", cfg.first_touch_mode))

    cfg.fresh_skip_min    = int(r.get("FRESH_SKIP_MIN", cfg.fresh_skip_min))
    cfg.fetch_retries     = int(r.get("FETCH_RETRIES", cfg.fetch_retries))
    cfg.fetch_retry_wait_sec = int(r.get("FETCH_RETRY_WAIT", cfg.fetch_retry_wait_sec))
    cfg.missing_data_policy = str(r.get("MISSING_DATA_POLICY", cfg.missing_data_policy)).lower()

    cfg.vol_ma_window     = int(r.get("VOL_MA_WINDOW", cfg.vol_ma_window))
    cfg.overhigh_lookback_min = int(r.get("OVERHIGH_LOOKBACK_MIN", cfg.overhigh_lookback_min))
    cfg.rsi_len           = int(r.get("RSI_LEN", cfg.rsi_len))
    cfg.macd_fast         = int(r.get("MACD_FAST", cfg.macd_fast))
    cfg.macd_slow         = int(r.get("MACD_SLOW", cfg.macd_slow))
    cfg.macd_signal       = int(r.get("MACD_SIGNAL", cfg.macd_signal))

    # new: allow overriding endpoint & product filter (if you use it later)
    cfg.coinbase_endpoint = r.get("COINBASE_ENDPOINT", cfg.coinbase_endpoint)
    return cfg


# ----------------------------- Helpers -----------------------------
def ensure_dir(p: str) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)

def to_unix_s(ts_val) -> Optional[int]:
    if ts_val is None:
        return None
    if isinstance(ts_val, (int, float)):
        return int(ts_val / 1000) if ts_val > 1e10 else int(ts_val)
    if isinstance(ts_val, str):
        try:
            if ts_val.isdigit():
                return to_unix_s(int(ts_val))
            return int(dt.datetime.fromisoformat(ts_val.replace("Z", "+00:00")).timestamp())
        except Exception:
            return None
    return None

def _open(path: str):
    return gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, "r", encoding="utf-8")

def read_json_or_jsonl(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with _open(path) as f:
        txt = f.read()
        if txt.lstrip().startswith("["):
            try:
                data = json.loads(txt)
                if isinstance(data, list):
                    out += [d for d in data if isinstance(d, dict)]
            except Exception:
                pass
        else:
            for line in txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    for r in out:
        r.setdefault("__source__", path)
    return out

def normalize_detection(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sym = raw.get("product_id") or raw.get("symbol") or raw.get("pair") or raw.get("ticker")
    price = raw.get("price") or raw.get("last_price") or raw.get("p") or raw.get("detected_price")
    ts = raw.get("timestamp") or raw.get("ts") or raw.get("detected_at") or raw.get("t_detected") or raw.get("time")
    ts = to_unix_s(ts)
    try:
        price = float(price)
    except Exception:
        return None
    if not sym or price is None or ts is None:
        return None
    return {"product_id": str(sym), "price": price, "detected_at": int(ts), "raw": raw}


# ----------------------------- Market / Indicators -----------------------------
def fetch_coinbase_candles(product_id: str, start_s: int, end_s: int,
                           granularity: int = 60,
                           endpoint: str = "https://api.exchange.coinbase.com") -> pd.DataFrame:
    url = f"{endpoint}/products/{product_id}/candles"
    params = {
        "granularity": granularity,
        "start": dt.datetime.fromtimestamp(start_s, tz=dt.timezone.utc).isoformat(),
        "end":   dt.datetime.fromtimestamp(end_s,   tz=dt.timezone.utc).isoformat(),
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    rows = list(reversed(data))  # API returns newest->oldest
    df = pd.DataFrame(rows, columns=["time", "low", "high", "open", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df.set_index("time")

def rsi_wilder(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/length, adjust=False).mean()
    roll_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = roll_up / (roll_down.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.bfill()

def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


# ----------------------------- Simulation -----------------------------
@dataclass
class TradeResult:
    product_id: str
    detected_at: int
    detection_price: float
    entry_price: float
    target_price: float
    stop_price: float
    outcome: str
    minutes_to_outcome: Optional[int]
    pnl_pct_after_fees: Optional[float]
    mfe_pct: Optional[float]
    mae_pct: Optional[float]
    rsi: Optional[float]
    macd_hist: Optional[float]
    source_file: Optional[str]
    notes: Optional[str] = None

def decide_first_touch(o, h, l, c, tp_price, sl_price, mode="conservative_stop_first"):
    hit_tp = h >= tp_price
    hit_sl = l <= sl_price
    if hit_tp and hit_sl:
        return "loss" if mode == "conservative_stop_first" else "win"
    elif hit_tp:
        return "win"
    elif hit_sl:
        return "loss"
    return None

def simulate_trade_on_candles(df: pd.DataFrame,
                              entry_price: float,
                              tp_pct: float,
                              sl_pct: float,
                              fee_bps_roundtrip: float,
                              first_touch_mode: str,
                              max_hold_min: int):
    tp_price = entry_price * (1 + tp_pct / 100.0)
    sl_price = entry_price * (1 - sl_pct / 100.0)
    mfe = -1e9
    mae = 1e9
    for i, (_, row) in enumerate(df.iterrows()):
        o, h, l, c = row["open"], row["high"], row["low"], row["close"]
        mfe = max(mfe, (h / entry_price - 1) * 100.0)
        mae = min(mae, (l / entry_price - 1) * 100.0)
        decision = decide_first_touch(o, h, l, c, tp_price, sl_price, mode=first_touch_mode)
        if decision is not None:
            gross = (tp_pct if decision == "win" else -sl_pct)
            net = gross - (fee_bps_roundtrip / 100.0)
            return decision, i + 1, net, mfe, mae
        if (i + 1) >= max_hold_min:
            exit_price = c
            gross = (exit_price / entry_price - 1) * 100.0
            net = gross - (fee_bps_roundtrip / 100.0)
            return "timeout", i + 1, net, mfe, mae
    # guarantee no 'bad-data' in final outputs; treat as timeout
    return "timeout", None, None, mfe if mfe != -1e9 else None, mae if mae != 1e9 else None


# ----------------------------- Main -----------------------------
def run(cfg: Config):
    ensure_dir(cfg.out_dir)

    recs = read_json_or_jsonl(cfg.detections_path)
    detections = [normalize_detection(r) for r in recs]
    detections = [d for d in detections if d is not None]

    now_s = int(dt.datetime.now(dt.timezone.utc).timestamp())
    cutoff = now_s - cfg.lookback_days * 86400
    detections = [d for d in detections if d["detected_at"] >= cutoff]
    if cfg.fresh_skip_min > 0:
        detections = [d for d in detections if d["detected_at"] <= (now_s - cfg.fresh_skip_min * 60)]

    if not detections:
        print("[info] No detections in window.")
        return

    print(f"[info] Loaded {len(detections)} detections. Processing…")

    rows: List[TradeResult] = []
    total = len(detections)

    for i, d in enumerate(detections, 1):
        if i == 1 or i % 5 == 0 or i == total:
            ts_str = dt.datetime.fromtimestamp(d["detected_at"], tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
            print(f"[{i}/{total}] {d['product_id']} @ {ts_str}")

        pid = d["product_id"]
        price = d["price"]
        det_at = d["detected_at"]
        src = d["raw"].get("__source__")

        # entry: detection price + slippage (bps)
        entry = price * (1 + cfg.slip_bps / 10000.0)

        # candle windows
        history_span_min = max(cfg.overhigh_lookback_min, cfg.rsi_len, cfg.macd_slow)
        start = det_at - history_span_min * cfg.granularity_sec
        end = det_at + cfg.max_hold_min * cfg.granularity_sec

        # fetch with retries
        try:
            attempts = 0
            while True:
                try:
                    hist = fetch_coinbase_candles(pid, start, det_at + cfg.granularity_sec,
                                                  cfg.granularity_sec, cfg.coinbase_endpoint)
                    fwd = fetch_coinbase_candles(pid, det_at, end,
                                                 cfg.granularity_sec, cfg.coinbase_endpoint)
                    break
                except Exception:
                    attempts += 1
                    if attempts > cfg.fetch_retries:
                        raise
                    time.sleep(cfg.fetch_retry_wait_sec)
        except Exception:
            # map to policy (loss/timeout/skip) — but never surface 'bad-data'
            policy = cfg.missing_data_policy
            outcome = "loss" if policy == "loss" else ("timeout" if policy == "timeout" else "timeout")
            rows.append(TradeResult(
                product_id=pid, detected_at=det_at, detection_price=price,
                entry_price=entry,
                target_price=entry * (1 + cfg.tp_pct / 100.0),
                stop_price=entry * (1 - cfg.sl_pct / 100.0),
                outcome=outcome, minutes_to_outcome=None, pnl_pct_after_fees=None,
                mfe_pct=None, mae_pct=None, rsi=None, macd_hist=None,
                source_file=src, notes="fetch-failed"
            ))
            continue

        # indicators snapshot (context only)
        close = hist["close"]
        rsi = rsi_wilder(close, cfg.rsi_len).iloc[-1]
        _, _, mac_hist = macd(close, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)

        # simulate (guaranteed to return win|loss|timeout)
        outcome, mins, pnl, mfe, mae = simulate_trade_on_candles(
            fwd, entry, cfg.tp_pct, cfg.sl_pct, cfg.fee_bps, cfg.first_touch_mode, cfg.max_hold_min
        )

        rows.append(TradeResult(
            product_id=pid, detected_at=det_at, detection_price=price,
            entry_price=entry,
            target_price=entry * (1 + cfg.tp_pct / 100.0),
            stop_price=entry * (1 - cfg.sl_pct / 100.0),
            outcome=outcome, minutes_to_outcome=mins, pnl_pct_after_fees=pnl,
            mfe_pct=mfe, mae_pct=mae,
            rsi=float(rsi), macd_hist=float(mac_hist.iloc[-1]),
            source_file=src
        ))

    # write outputs
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_csv = os.path.join(cfg.out_dir, f"chronovore_research_{ts}.csv")
    df = pd.DataFrame([asdict(r) for r in rows])
    df.insert(1, "detected_at_utc", pd.to_datetime(df["detected_at"], unit="s", utc=True).astype(str))
    df.to_csv(out_csv, index=False)

    print(f"Saved {len(df)} results → {out_csv}")
    print(df["outcome"].value_counts())


# entrypoint
if __name__ == "__main__":
    cfg = Config()
    cfg = _apply_envelope_overrides(cfg)
    run(cfg)
