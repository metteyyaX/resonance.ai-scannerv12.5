# Resonance.ai 🚨 Breakout Scanner 🚨

Real-time crypto breakout detection powered by **Resonance.ai** (beta version pre-ML).
This scanner monitors Coinbase trading pairs and sends instant breakout alerts to Discord.

---

## ✨ Features

- **Multi-band breakout detection**
  - Fast (10 candles)
  - Medium (15 candles)
  - Slow (20 candles)
- **Two alert modes**
  - Simple mode → clean, quick alerts
  - Pro mode → detailed analytics (volume ratios, over-max %, $/min flow)
- **Discord integration** → rich alerts sent directly to your server
- **Volume protection** → filters low-liquidity pairs with a dollar/minute floor
- **Lightweight loop** → optimized for cloud platforms like Railway

---

## 🚀 Quick Start

1. Clone the repo:

```bash
git clone https://github.com/yourname/resonance-breakout-scanner.git
cd resonance-breakout-scanner
```

1.1 You may need to run this too

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables:

| Variable        | Description                       | Default    |
| --------------- | --------------------------------- | ---------- |
| SIMPLE_MODE     | 1 = simple alerts, 0 = pro alerts | 1          |
| ABS_VOL_MIN_USD | Minimum $/min volume filter       | 2000       |
| DISCORD_WEBHOOK | Your Discord webhook URL          | (required) |

Example `.env` file:

```
SIMPLE_MODE=1
ABS_VOL_MIN_USD=2000
DISCORD_WEBHOOK=https://discord.com/api/webhooks/yourwebhookid/yourwebhooktoken
```

4. Run the scanner:

```bash
python breakout_scanner.py
```

---

## 📊 Alert Examples

**Simple Mode**

```
🚨 BREAKOUT DETECTED 🚨
Pair: `DOGE-USD`
Δ: `+2.45%` | W: `1.30%`
Bands: FAST, MEDIUM
Time: 12:34:56 UTC
```

**Pro Mode**

```
🚨 BREAKOUT DETECTED 🚨
Pair: `DOGE-USD`
Price: $0.08234500
Δ: +2.45%  |  W: 1.30%
Candle: 60s
• FAST (n=10): over max by 1.45%, vol 1200 vs avg 850 (x1.41), $98,000/min
• MEDIUM (n=15): over max by 2.10%, vol 1800 vs avg 1050 (x1.71), $148,000/min
Time: 12:34:56 UTC
```

---

## ⚙️ Configuration Parameters

| Parameter       | Description                                   | Default    |
| --------------- | --------------------------------------------- | ---------- |
| SIMPLE_MODE     | 1 = simple alerts, 0 = pro alerts             | 1          |
| ABS_VOL_MIN_USD | Minimum dollar/minute volume to consider pair | 2000       |
| DISCORD_WEBHOOK | Discord webhook URL for alerts                | (required) |

---

## 🔧 Discord Setup

To receive alerts in your Discord server:

1. Create a Webhook
2. In Discord, right-click your channel → Edit Channel
3. Go to Integrations → Webhooks → New Webhook
4. Name it (e.g., Resonance Alerts)
5. Copy the Webhook URL
6. Add the Webhook URL to the scanner via the `DISCORD_WEBHOOK` environment variable

Run the scanner, and breakout alerts will flow directly into your Discord channel.

---

## 🔧 Telegram Setup

1. Create a Telegram Bot
2. Message **[@BotFather](https://t.me/BotFather)** on Telegram.  
3. Use the `/newbot` command.  
4. Follow the prompts to create your bot.  
5. Copy the **bot token** (it looks like `123456789:ABCDEF...`).  

---

###  Get Your Chat ID

#### Option A - Personal Chat
1. Send a message to your bot.  
2. Visit: https://api.telegram.org/bot
3. Look for your `chat.id` in the JSON response.  

#### Option B - Channel/Group
1. Add your bot to the channel or group as **admin**.  
2. The chat ID will be **negative** (e.g., `-1001234567890`).  

---

### Update Configuration
Replace the placeholder values in your script:  

```python
TELEGRAM_BOT_TOKEN = "ADD YOUR TELEGRAM BOT TOKEN HERE"
TELEGRAM_CHAT_ID = "ADD YOUR TELEGRAM CHAT ID HERE"
```

---

## 📦 Deployment

### Local (Python 3.10+)

```bash
git clone https://github.com/yourname/resonance-breakout-scanner.git
cd resonance-breakout-scanner
pip install -r requirements.txt
python breakout_scanner.py
```

### Cloud (Railway / Render / etc.) (More on this coming soon)

- Add environment variables in your service dashboard
- Deploy the script; logs will show scanning activity
- Alerts will be sent to your Discord channel

---

## 🛠 Troubleshooting

- Ensure your Discord webhook URL is correct and active.
- Check your internet connection and API rate limits.
- Adjust `ABS_VOL_MIN_USD` if you see too many or too few alerts.
- Use simple mode (`SIMPLE_MODE=1`) for faster, less detailed alerts.
- Use pro mode (`SIMPLE_MODE=0`) for detailed analytics.

---

## 🔮 Roadmap

- Auto-trading integration / dry run learning tool
- Smarter auto coin list rotation (top gainers/losers)
- Machine learning plugin (**WaveScore and HFT hunter**)
- Parachute Bot (scans trades, sets limit orders, cancels, and quick market sells within 1 sec)
- Soliton.ai Trading Arsenal: a free ML-powered autotrader/HFT skimmer with multiple strategies and modes (MONK, HAWK, MADMAN)

---

## 📜 License

This project is licensed under the **Apache License 2.0** — free and open source.
You are free to use, modify, and distribute this code (including commercially),
provided you keep the copyright notice and license text.

⚠️ No warranties or guarantees are provided. Use at your own risk. Not financial advice. Always paper trade after making changes.
