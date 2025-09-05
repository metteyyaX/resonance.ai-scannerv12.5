# === Resonance.ai v12.5 Breakout Analytics ===
# Δ (percent_change): % price change from first to last candle
# W (band_width): volatility range = (high - low) / end_price * 100
# High Δ = trending strongly (potential breakout)
# High W = volatile (good for faster scalping)
import socketio
import threading
from flask import Flask
from datetime import timedelta, datetime, timezone
import time
import requests
import json
from pathlib import Path
import os
import statistics

# ===== Alert display mode =====
# Default is Simple Mode - standard detection readout
SIMPLE_MODE = os.getenv("SIMPLE_MODE", "1") == "0"   # set SIMPLE_MODE=0 to enable Pro mode

# Absolute dollar-volume floor (quote currency per 1m candle).
# Can be overridden with a Railway env var: ABS_VOL_MIN_USD
ABSOLUTE_DOLLAR_VOLUME_MIN = float(os.getenv("ABS_VOL_MIN_USD", "2000"))

print(f"[Config] Absolute $/min volume floor = ${ABSOLUTE_DOLLAR_VOLUME_MIN:,.0f}")

SCRIPT_DIR = Path(__file__).resolve().parent
# [No file saving on mobile/cloud]

def log_coin_scan(symbol, change_1h=None, band_width=None, breakout_status=None):
    msg = f"[SKIPPED] {symbol} | "
    if change_1h is not None:
        msg += f"1H Δ: {change_1h:.3f}% | "
    if band_width is not None:
        msg += f"Band W: {band_width:.3f}% | "
    if breakout_status is not None:
        msg += f"Breakout: {'✔' if breakout_status else '✘'}"
    print(msg, flush=True)


# === CONFIGURATION === #
COINS = [
    
"00-USD",
"1INCH-USD",
"A8-USD",
"AAVE-USD",
"ABT-USD",
"ACH-USD",
"ACS-USD",
"ACX-USD",
"ADA-USD",
"AERGO-USD",
"AERO-USD",
"AGLD-USD",
"AIOZ-USD",
"AKT-USD",
"ALCX-USD",
"ALEO-USD",
"ALEPH-USD",
"ALGO-USD",
"ALICE-USD",
"ALT-USD",
"AMP-USD",
"ANKR-USD",
"APE-USD",
"API3-USD",
"APT-USD",
"ARB-USD",
"ARKM-USD",
"ARPA-USD",
"ASM-USD",
"AST-USD",
"ATH-USD",
"ATOM-USD",
"AUCTION-USD",
"AUDIO-USD",
"AURORA-USD",
"AVAX-USD",
"AVT-USD",
"AXL-USD",
"AXS-USD",
"B3-USD",
"BADGER-USD",
"BAL-USD",
"BAND-USD",
"BAT-USD",
"BCH-USD",
"BERA-USD",
"BICO-USD",
"BIGTIME-USD",
"BIO-USD",
"BLAST-USD",
"BLUR-USD",
"BLZ-USD",
"BNKR-USD",
"BNT-USD",
"BOBA-USD",
"BONK-USD",
"BTC-USD",
"BTRST-USD",
"C98-USD",
"CAKE-USD",
"CBETH-USD",
"CELR-USD",
"CGLD-USD",
"CHZ-USD",
"CLANKER-USD",
"CLV-USD",
"COMP-USD",
"COOKIE-USD",
"CORECHAIN-USD",
"COTI-USD",
"COW-USD",
"CRO-USD",
"CRV-USD",
"CTSI-USD",
"CTX-USD",
"CVC-USD",
"CVX-USD",
"DAI-USD",
"DASH-USD",
"DEGEN-USD",
"DEXT-USD",
"DIA-USD",
"DIMO-USD",
"DNT-USD",
"DOGE-USD",
"DOGINME-USD",
"DOT-USD",
"DRIFT-USD",
"EDGE-USD",
"EGLD-USD",
"EIGEN-USD",
"ELA-USD",
"ENA-USD",
"ENS-USD",
"EOS-USD",
"ERA-USD",
"ERN-USD",
"ETC-USD",
"ETH-USD",
"ETHFI-USD",
"FAI-USD",
"FARM-USD",
"FARTCOIN-USD",
"FET-USD",
"FIDA-USD",
"FIL-USD",
"FIS-USD",
"FLOKI-USD",
"FLOW-USD",
"FLR-USD",
"FORT-USD",
"FORTH-USD",
"FOX-USD",
"FX-USD",
"G-USD",
"GFI-USD",
"GHST-USD",
"GIGA-USD",
"GLM-USD",
"GMT-USD",
"GNO-USD",
"GODS-USD",
"GRT-USD",
"GST-USD",
"GTC-USD",
"HBAR-USD",
"HFT-USD",
"HIGH-USD",
"HNT-USD",
"HOME-USD",
"HONEY-USD",
"HOPR-USD",
"ICP-USD",
"IDEX-USD",
"ILV-USD",
"IMX-USD",
"INDEX-USD",
"INJ-USD",
"INV-USD",
"IO-USD",
"IOTX-USD",
"IP-USD",
"JASMY-USD",
"JITOSOL-USD",
"JTO-USD",
"KAITO-USD",
"KARRAT-USD",
"KAVA-USD",
"KERNEL-USD",
"KEYCAT-USD",
"KNC-USD",
"KRL-USD",
"KSM-USD",
"L3-USD",
"LA-USD",
"LCX-USD",
"LDO-USD",
"LINK-USD",
"LOKA-USD",
"LPT-USD",
"LQTY-USD",
"LRC-USD",
"LRDS-USD",
"LSETH-USD",
"LTC-USD",
"MAGIC-USD",
"MANA-USD",
"MANTLE-USD",
"MASK-USD",
"MATH-USD",
"MATIC-USD",
"MDT-USD",
"ME-USD",
"METIS-USD",
"MINA-USD",
"MKR-USD",
"MLN-USD",
"MNDE-USD",
"MOG-USD",
"MOODENG-USD",
"MORPHO-USD",
"MPLX-USD",
"MSOL-USD",
"MUSE-USD",
"NCT-USD",
"NEAR-USD",
"NEON-USD",
"NEWT-USD",
"NKN-USD",
"NMR-USD",
"OCEAN-USD",
"OGN-USD",
"OMNI-USD",
"ONDO-USD",
"OP-USD",
"ORCA-USD",
"OSMO-USD",
"OXT-USD",
"PAXG-USD",
"PENDLE-USD",
"PENGU-USD",
"PEPE-USD",
"PERP-USD",
"PIRATE-USD",
"PLU-USD",
"PNG-USD",
"PNUT-USD",
"POL-USD",
"POLS-USD",
"POND-USD",
"POPCAT-USD",
"POWR-USD",
"PRCL-USD",
"PRIME-USD",
"PRO-USD",
"PROMPT-USD",
"PUMP-USD",
"PUNDIX-USD",
"PYR-USD",
"PYTH-USD",
"QI-USD",
"QNT-USD",
"RAD-USD",
"RARE-USD",
"RARI-USD",
"RED-USD",
"RENDER-USD",
"REQ-USD",
"REZ-USD",
"RLC-USD",
"RONIN-USD",
"ROSE-USD",
"RPL-USD",
"RSC-USD",
"RSR-USD",
"S-USD",
"SAFE-USD",
"SAND-USD",
"SD-USD",
"SEAM-USD",
"SEI-USD",
"SHDW-USD",
"SHIB-USD",
"SHPING-USD",
"SKL-USD",
"SKY-USD",
"SNX-USD",
"SOL-USD",
"SPA-USD",
"SPELL-USD",
"SPK-USD",
"SQD-USD",
"STG-USD",
"STORJ-USD",
"STRK-USD",
"STX-USD",
"SUI-USD",
"SUKU-USD",
"SUPER-USD",
"SUSHI-USD",
"SWELL-USD",
"SWFTC-USD",
"SXT-USD",
"SYRUP-USD",
"T-USD",
"TAO-USD",
"TIA-USD",
"TIME-USD",
"TNSR-USD",
"TOSHI-USD",
"TRAC-USD",
"TRB-USD",
"TREE-USD",
"TRU-USD",
"TRUMP-USD",
"TURBO-USD",
"UMA-USD",
"UNI-USD",
"USDS-USD",
"USDT-USD",
"VARA-USD",
"VELO-USD",
"VET-USD",
"VOXEL-USD",
"VTHO-USD",
"VVV-USD",
"W-USD",
"WAXL-USD",
"WCFG-USD",
"WELL-USD",
"WIF-USD",
"WLD-USD",
"XCN-USD",
"XLM-USD",
"XRP-USD",
"XTZ-USD",
"XYO-USD",
"YFI-USD",
"ZEC-USD",
"ZEN-USD",
"ZETA-USD",
"ZETACHAIN-USD",
"ZK-USD",
"ZORA-USD",
"ZRO-USD",
"ZRX-USD"

]

USDC_ONLY_COINS = []

DISCORD_WEBHOOK = "ADD YOUR DISCORD WEBHOOK HERE"

# === Telegram Configuration ===
TELEGRAM_BOT_TOKEN = "ADD YOUR TELEGRAM BOT TOKEN HERE"  # Get from @BotFather
TELEGRAM_CHAT_ID = "ADD YOUR TELEGRAM CHAT ID HERE"      # Your chat ID or channel ID

# === Breakout Scanner Parameters ===
CANDLE_INTERVAL = 60  # seconds

CANDLE_COUNT_FAST = 10
CANDLE_COUNT_MEDIUM = 15
CANDLE_COUNT_SLOW = 20

BREAKOUT_THRESHOLD_FAST = 0.013
BREAKOUT_THRESHOLD_MEDIUM = 0.018
BREAKOUT_THRESHOLD_SLOW = 0.024

VOLUME_SPIKE_RATIO_FAST = 1.3
VOLUME_SPIKE_RATIO_MEDIUM = 1.7
VOLUME_SPIKE_RATIO_SLOW = 2.2

lookback_candles = 10  # 6-8= jumpy 10-20= quiet  mode

BASE_URL = "https://api.exchange.coinbase.com"

def get_candles(product_id, granularity=CANDLE_INTERVAL):
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(seconds=granularity * lookback_candles)

        url = f"{BASE_URL}/products/{product_id}/candles"
        params = {
            "granularity": granularity,
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"❌ Error fetching candles for {product_id}: HTTP {response.status_code}", flush=True)
            return []

        data = response.json()
        if not isinstance(data, list) or not data:
            print(f"⚠️ API returned no/bad data for {product_id}: {data}", flush=True)
            return []

        data.sort(key=lambda c: c[0])
        return data
    except Exception as e:
        print(f"❌ Exception fetching candles for {product_id}: {e}", flush=True)
        return []

def send_discord_alert(pair, price, vol_info):
    data = {
        "content": f"🚨 **BREAKOUT DETECTED** 🚨\n**Pair**: `{pair}`\n**Price**: `${price:.8f}`\n**Vol Spike**: {vol_info}\n**Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
    }
    requests.post(DISCORD_WEBHOOK, json=data)

def send_telegram_alert(message: str):
    """Send alert message to Telegram bot"""
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return  # Skip if not configured
            
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Telegram API error: {response.status_code} - {response.text}", flush=True)
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}", flush=True)

def is_breakout_band(cset, breakout_threshold, volume_spike_ratio):
    """
    Returns (hit: bool, info: dict)
    info includes: window, last_close, max_high, pct_over, last_vol, avg_vol, vol_ratio, usd_per_min
    """
    if len(cset) < 3:
        return False, None

    highs   = [c[2] for c in cset]
    closes  = [c[4] for c in cset]
    volumes = [c[5] for c in cset]

    if len(highs) < 2 or len(volumes) < 2:
        return False, None

    max_high    = max(highs[:-1])           # highest high before last candle
    last_close  = closes[-1]                # last close
    avg_vol     = statistics.mean(volumes[:-1])
    last_vol    = volumes[-1]
    usd_per_min = last_vol * last_close

    pct_over    = ((last_close / max_high) - 1.0) * 100 if max_high > 0 else 0.0
    vol_ratio   = (last_vol / avg_vol) if avg_vol > 0 else 0.0

    hit = (
        last_close > max_high * (1 + breakout_threshold) and
        last_vol   > avg_vol   * volume_spike_ratio and
        usd_per_min >= ABSOLUTE_DOLLAR_VOLUME_MIN
    )

    info = {
        "window": len(cset),
        "last_close": float(last_close),
        "max_high": float(max_high),
        "pct_over": float(pct_over),
        "last_vol": float(last_vol),
        "avg_vol": float(avg_vol),
        "vol_ratio": float(vol_ratio),
        "usd_per_min": float(usd_per_min),
    }
    return hit, info



from dataclasses import dataclass

@dataclass
class BandStats:
    over_max_pct: float
    vol: float
    avg_vol: float
    vol_mult: float
    dollars_per_min: float
    window: int

def stats_from_info(info: dict) -> "BandStats":
    """Convert legacy info dict to BandStats to avoid shared-state bugs and make formatting explicit."""
    if not info:
        return None
    return BandStats(
        over_max_pct=float(info.get("pct_over", 0.0)),
        vol=float(info.get("last_vol", 0.0)),
        avg_vol=float(info.get("avg_vol", 0.0)),
        vol_mult=float(info.get("vol_ratio", 0.0)),
        dollars_per_min=float(info.get("usd_per_min", 0.0)),
        window=int(info.get("window", 0)),
    )

from dataclasses import dataclass

@dataclass
class BandStats:
    over_max_pct: float
    vol: float
    avg_vol: float
    vol_mult: float
    dollars_per_min: float
    window: int

def stats_from_info(info: dict) -> "BandStats":
    """Convert legacy info dict to BandStats to avoid shared-state bugs and make formatting explicit."""
    if not info:
        return None
    return BandStats(
        over_max_pct=float(info.get("pct_over", 0.0)),
        vol=float(info.get("last_vol", 0.0)),
        avg_vol=float(info.get("avg_vol", 0.0)),
        vol_mult=float(info.get("vol_ratio", 0.0)),
        dollars_per_min=float(info.get("usd_per_min", 0.0)),
        window=int(info.get("window", 0)),
    )
def build_alert_message_simple(
    pair, price, percent_change, band_width, band_details, candle_interval_sec
):
    bands_str = ", ".join([bd["name"] for bd in band_details]) if band_details else "—"
    return "\n".join([
        "🚨 **BREAKOUT DETECTED** 🚨",
        f"**Pair**: `{pair}`",
        f"**Δ**: `{percent_change:.2f}%` | **W**: `{band_width:.2f}%`",
        f"**Bands**: {bands_str}",
        f"**Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}",
    ])


def build_alert_message_pro(
    pair, price, percent_change, band_width, band_details, candle_interval_sec
):
    
    lines = []
    lines.append("🚨 **BREAKOUT DETECTED** 🚨")
    lines.append(f"**Pair**: `{pair}`")
    lines.append(f"**Price**: `${price:.8f}`")
    lines.append(f"**Δ**: `{percent_change:.2f}%`  |  **W**: `{band_width:.2f}%`")
    lines.append(f"**Candle**: `{candle_interval_sec}s`")

    
    for bd in band_details:
        name = bd["name"]
        if "stats" in bd and bd["stats"] is not None:
            s = bd["stats"]
            lines.append(
                f"• **{name}** (n={s.window}): "
                f"over max by `{s.over_max_pct:.2f}%`, "
                f"vol `{s.vol:.0f}` vs avg `{s.avg_vol:.0f}` "
                f"(x`{s.vol_mult:.2f}`), "
                f"`${s.dollars_per_min:,.0f}/min`"
            )
        else:
            info = bd["info"]
            lines.append(
                f"• **{name}** (n={info['window']}): "
                f"over max by `{info['pct_over']:.2f}%`, "
                f"vol `{info['last_vol']:.0f}` vs avg `{info['avg_vol']:.0f}` "
                f"(x`{info['vol_ratio']:.2f}`), "
                f"`${info['usd_per_min']:,.0f}/min`"
            )
    lines.append(f"**Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
    return "\n".join(lines)


def build_alert_message(
    pair, price, percent_change, band_width, band_details, candle_interval_sec
):
    if SIMPLE_MODE:
        return build_alert_message_simple(
            pair, price, percent_change, band_width, band_details, candle_interval_sec
        )
    else:
        return build_alert_message_pro(
            pair, price, percent_change, band_width, band_details, candle_interval_sec
        )


def send_discord_rich(message: str):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
    except Exception as e:
        print(f"❌ Failed to send Discord message: {e}", flush=True)


# === Main Loop === #
print("\n--- Resonance.ai Breakout Scanner Activated ---")
while True:
    for pair in COINS + USDC_ONLY_COINS:
        try:
            print(f"Scanning {pair}...")
            candles = get_candles(pair)

            if not candles:
                log_coin_scan(pair)
                continue

            start_price = candles[0][4]
            end_price = candles[-1][4]
            percent_change = ((end_price - start_price) / start_price) * 100

            highs = [c[2] for c in candles]
            lows = [c[3] for c in candles]
            band_width = (max(highs) - min(lows)) / end_price * 100

# --- Breakout detection (returns details) ---
            b1, i1 = is_breakout_band(candles[-CANDLE_COUNT_FAST:],   BREAKOUT_THRESHOLD_FAST,   VOLUME_SPIKE_RATIO_FAST)
            b2, i2 = is_breakout_band(candles[-CANDLE_COUNT_MEDIUM:], BREAKOUT_THRESHOLD_MEDIUM, VOLUME_SPIKE_RATIO_MEDIUM)
            b3, i3 = is_breakout_band(candles[-CANDLE_COUNT_SLOW:],   BREAKOUT_THRESHOLD_SLOW,   VOLUME_SPIKE_RATIO_SLOW)

            band_details = []
            if b1: band_details.append({"name": "FAST",   "stats": stats_from_info(i1)})
            if b2: band_details.append({"name": "MEDIUM", "stats": stats_from_info(i2)})
            if b3: band_details.append({"name": "SLOW",   "stats": stats_from_info(i3)})

            if band_details:
                print(
                    f"[SELECTED] {pair} | Δ: {percent_change:.2f}% | W: {band_width:.2f}% | "
                    f"Hits: {[bd['name'] for bd in band_details]}",
                    flush=True
                )
                msg = build_alert_message(
                    pair=pair,
                    price=end_price,
                    percent_change=percent_change,
                    band_width=band_width,
                    band_details=band_details,
                    candle_interval_sec=CANDLE_INTERVAL
                )
                # Send to both Discord and Telegram
                send_discord_rich(msg)
                send_telegram_alert(msg)
            else:
                print(f"{pair} | Δ: {percent_change:.2f}% | W: {band_width:.2f}%")
                
        except Exception as e:
            print(f"Error processing {pair}: {e}")

    print("Sleeping 2 seconds...\n")
    time.sleep(2)

# WebUI Integration Class
class WebUIIntegration:
    def __init__(self, socketio_client=None):
        self.socketio_client = socketio_client
        self.stats = {
            'total_scanned': 0,
            'total_alerts': 0,
            'breakouts_today': 0,
            'start_time': datetime.now(timezone.utc),
        }
        
    def emit_scan_result(self, symbol, change, band_width):
        """Emit scan result to WebUI"""
        if not self.socketio_client:
            return
            
        data = {
            'type': 'scan_result',
            'symbol': symbol,
            'change': float(change),
            'band_width': float(band_width),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.socketio_client.emit('scan_update', data)
            self.stats['total_scanned'] += 1
        except Exception as e:
            print(f"WebUI emit error: {e}")
    
    def emit_breakout_alert(self, symbol, price, change, band_width, bands):
        """Emit breakout alert to WebUI"""
        if not self.socketio_client:
            return
            
        data = {
            'type': 'breakout_alert',
            'symbol': symbol,
            'price': float(price),
            'change': float(change),
            'band_width': float(band_width),
            'bands': bands,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.socketio_client.emit('breakout_alert', data)
            self.stats['total_alerts'] += 1
            self.stats['breakouts_today'] += 1
        except Exception as e:
            print(f"WebUI emit error: {e}")
    
    def get_stats(self):
        """Get current statistics"""
        return self.stats.copy()

# Initialize WebUI integration
webui = WebUIIntegration()

# Modified scanner settings that can be controlled from WebUI
class ScannerSettings:
    def __init__(self):
        self.scan_interval = 2
        self.volume_floor = 2000.0
        self.alert_mode = 'simple'
        self.fast_threshold = 0.013
        self.medium_threshold = 0.018
        self.slow_threshold = 0.024
        self.fast_ratio = 1.3
        self.medium_ratio = 1.7
        self.slow_ratio = 2.2
        self.discord_webhook = ""
        self.telegram_token = ""
        self.telegram_chat_id = ""
        
    def update_from_webui(self, settings_dict):
        """Update settings from WebUI"""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                # Convert string values to appropriate types
                if key in ['scan_interval']:
                    setattr(self, key, int(value))
                elif key in ['volume_floor', 'fast_threshold', 'medium_threshold', 'slow_threshold', 
                           'fast_ratio', 'medium_ratio', 'slow_ratio']:
                    setattr(self, key, float(value))
                else:
                    setattr(self, key, str(value))
                    
        print(f"Settings updated: {settings_dict}")

# Global settings instance
settings = ScannerSettings()

# Modified main scanning function
def run_scanner_with_webui():
    """
    Modified version of your main scanning loop that integrates with WebUI
    Replace your existing main loop with this function
    """
    global settings, webui
    
    print("\n--- Resonance.ai Breakout Scanner with WebUI Integration ---")
    
    while True:
        if not scanner_running:  # This would be controlled by WebUI
            time.sleep(1)
            continue
            
        for pair in COINS + USDC_ONLY_COINS:
            try:
                print(f"Scanning {pair}...")
                candles = get_candles(pair)

                if not candles:
                    log_coin_scan(pair)
                    continue

                start_price = candles[0][4]
                end_price = candles[-1][4]
                percent_change = ((end_price - start_price) / start_price) * 100

                highs = [c[2] for c in candles]
                lows = [c[3] for c in candles]
                band_width = (max(highs) - min(lows)) / end_price * 100

                # Emit scan result to WebUI
                webui.emit_scan_result(pair, percent_change, band_width)

                # Use dynamic settings from WebUI
                b1, i1 = is_breakout_band(candles[-CANDLE_COUNT_FAST:], settings.fast_threshold, settings.fast_ratio)
                b2, i2 = is_breakout_band(candles[-CANDLE_COUNT_MEDIUM:], settings.medium_threshold, settings.medium_ratio)
                b3, i3 = is_breakout_band(candles[-CANDLE_COUNT_SLOW:], settings.slow_threshold, settings.slow_ratio)

                band_details = []
                band_names = []
                if b1: 
                    band_details.append({"name": "FAST", "stats": stats_from_info(i1)})
                    band_names.append("FAST")
                if b2: 
                    band_details.append({"name": "MEDIUM", "stats": stats_from_info(i2)})
                    band_names.append("MEDIUM")
                if b3: 
                    band_details.append({"name": "SLOW", "stats": stats_from_info(i3)})
                    band_names.append("SLOW")

                if band_details:
                    print(
                        f"[SELECTED] {pair} | Δ: {percent_change:.2f}% | W: {band_width:.2f}% | "
                        f"Hits: {[bd['name'] for bd in band_details]}",
                        flush=True
                    )
                    
                    # Build alert message using current settings
                    msg = build_alert_message(
                        pair=pair,
                        price=end_price,
                        percent_change=percent_change,
                        band_width=band_width,
                        band_details=band_details,
                        candle_interval_sec=CANDLE_INTERVAL
                    )
                    
                    # Send alerts (Discord/Telegram)
                    if settings.discord_webhook:
                        send_discord_rich(msg)
                    if settings.telegram_token and settings.telegram_chat_id:
                        send_telegram_alert(msg)
                    
                    # Emit to WebUI
                    webui.emit_breakout_alert(pair, end_price, percent_change, band_width, band_names)
                else:
                    print(f"{pair} | Δ: {percent_change:.2f}% | W: {band_width:.2f}%")
                    
            except Exception as e:
                print(f"Error processing {pair}: {e}")

        print(f"Sleeping {settings.scan_interval} seconds...\n")
        time.sleep(settings.scan_interval)

# WebUI Server Integration
def start_webui_server():
    """Start the WebUI server in a separate thread"""
    import subprocess
    import sys
    
    try:
        # Start the Flask server
        subprocess.Popen([sys.executable, "app.py"])
        print("🌐 WebUI Server starting at http://localhost:5000")
    except Exception as e:
        print(f"Failed to start WebUI server: {e}")

# Settings API endpoint integration
def handle_webui_settings_update(new_settings):
    """Handle settings update from WebUI"""
    global settings, ABSOLUTE_DOLLAR_VOLUME_MIN, SIMPLE_MODE
    
    settings.update_from_webui(new_settings)
    
    # Update global variables
    ABSOLUTE_DOLLAR_VOLUME_MIN = settings.volume_floor
    SIMPLE_MODE = (settings.alert_mode == 'simple')
    
    # Update alert configurations
    global DISCORD_WEBHOOK, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    DISCORD_WEBHOOK = settings.discord_webhook
    TELEGRAM_BOT_TOKEN = settings.telegram_token
    TELEGRAM_CHAT_ID = settings.telegram_chat_id

# WebSocket client for communicating with WebUI
def setup_socketio_client():
    """Setup SocketIO client for WebUI communication"""
    global webui
    
    try:
        sio = socketio.SimpleClient()
        sio.connect('http://localhost:5000')
        webui.socketio_client = sio
        print("✅ Connected to WebUI server")
        return sio
    except Exception as e:
        print(f"⚠️ Could not connect to WebUI server: {e}")
        return None

# Integration wrapper function
def run_with_webui_integration():
    """
    Main function to run the scanner with WebUI integration
    Replace your existing main execution with this
    """
    global webui, settings
    
    # Start WebUI server
    webui_thread = threading.Thread(target=start_webui_server, daemon=True)
    webui_thread.start()
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Setup WebSocket connection
    sio_client = setup_socketio_client()
    webui.socketio_client = sio_client
    
    # Run the scanner
    try:
        run_scanner_with_webui()
    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped by user")
        if sio_client:
            sio_client.disconnect()
    except Exception as e:
        print(f"❌ Scanner error: {e}")
        if sio_client:
            sio_client.disconnect()

# Usage Instructions:
"""
To integrate with your existing scanner:

1. Add these imports at the top of your resonance_scanner_v12_5.py:
   import socketio
   import threading
   from flask import Flask

2. Replace your existing main loop execution with:
   if __name__ == "__main__":
       run_with_webui_integration()

3. Install required packages:
   pip install flask flask-socketio python-socketio

4. Create the app.py file (from the Flask Backend artifact)

5. Start your scanner:
   python resonance_scanner_v12_5.py

6. Access WebUI at:
   http://localhost:5000

The WebUI will show:
- Real-time scanning results
- Live breakout alerts
- Configurable settings
- Performance statistics
- Alert testing capabilities
"""
