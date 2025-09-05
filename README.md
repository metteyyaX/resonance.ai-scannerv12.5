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

# Telegram Alert Setup Guide

This guide will walk you through setting up Telegram alerts for the Resonance.ai Breakout Scanner.

## 📋 Prerequisites

- A Telegram account
- The updated `resonance_scanner_v12_5.py` script with Telegram integration

## 🤖 Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather by clicking "Start" or sending `/start`
3. **Create a new bot** by sending the command:
   ```
   /newbot
   ```
4. **Choose a name** for your bot (e.g., "Resonance Breakout Alerts")
5. **Choose a username** for your bot (must end with "bot", e.g., "resonance_breakout_bot")
6. **Copy the bot token** that BotFather provides. It looks like:
   ```
   1234567890:ABCDEF1234567890abcdefghijklmnopqrstuvwxyz
   ```
   ⚠️ **Keep this token secure!** Anyone with this token can control your bot.

## 🔍 Step 2: Get Your Chat ID

### Method A: Personal Chat (Recommended for individual use)

1. **Find your bot** in Telegram using the username you created
2. **Send a message** to your bot (e.g., "Hello")
3. **Open your browser** and go to:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with the token from Step 1
4. **Find your chat ID** in the response. Look for something like:
   ```json
   {
     "message": {
       "chat": {
         "id": 123456789,
         "first_name": "Your Name",
         "type": "private"
       }
     }
   }
   ```
   Your chat ID is the number after `"id":` (e.g., `123456789`)

### Method B: Channel or Group Chat

1. **Create a channel or group** (or use an existing one)
2. **Add your bot** as an administrator with permission to send messages
3. **Send a message** in the channel/group mentioning your bot
4. **Get updates** using the same URL as Method A
5. **Find the chat ID** - it will be negative for channels/groups (e.g., `-1001234567890`)

### Method C: Using @userinfobot (Alternative)

1. **Forward a message** from your bot to `@userinfobot`
2. **Get your chat ID** from the response

## ⚙️ Step 3: Configure the Script

1. **Open** your `resonance_scanner_v12_5.py` file
2. **Find these lines** (around line 179-181):
   ```python
   TELEGRAM_BOT_TOKEN = "ADD YOUR TELEGRAM BOT TOKEN HERE"
   TELEGRAM_CHAT_ID = "ADD YOUR TELEGRAM CHAT ID HERE"
   ```
3. **Replace the placeholders** with your actual values:
   ```python
   TELEGRAM_BOT_TOKEN = "1234567890:ABCDEF1234567890abcdefghijklmnopqrstuvwxyz"
   TELEGRAM_CHAT_ID = "123456789"
   ```

### Example Configuration:
```python
# Personal chat
TELEGRAM_BOT_TOKEN = "1234567890:ABCDEF1234567890abcdefghijklmnopqrstuvwxyz"
TELEGRAM_CHAT_ID = "123456789"

# Channel/Group chat
TELEGRAM_BOT_TOKEN = "1234567890:ABCDEF1234567890abcdefghijklmnopqrstuvwxyz"
TELEGRAM_CHAT_ID = "-1001234567890"
```

## ✅ Step 4: Test Your Setup

1. **Save** your script with the updated configuration
2. **Run** the script:
   ```bash
   python resonance_scanner_v12_5.py
   ```
3. **Wait for a breakout alert** to be triggered
4. **Check your Telegram** - you should receive the same alerts that go to Discord

## 🔧 Troubleshooting

### Bot Not Sending Messages
- ✅ **Check bot token**: Ensure it's copied correctly without extra spaces
- ✅ **Check chat ID**: Make sure it's the correct number (positive for personal, negative for groups/channels)
- ✅ **Message your bot first**: For personal chats, you must send a message to the bot before it can message you
- ✅ **Bot permissions**: For groups/channels, ensure the bot has permission to send messages

### Getting Error Messages
- **`Chat not found`**: Your chat ID is incorrect
- **`Unauthorized`**: Your bot token is incorrect
- **`Bot was blocked by the user`**: You blocked the bot - unblock it in Telegram

### Script Still Working Without Telegram
If Telegram isn't configured properly, the script will continue working and send Discord alerts only. Check the console for error messages starting with "❌".

## 🎨 Customization Options

### Environment Variables (Optional)
Instead of hardcoding values, you can use environment variables:

```python
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
```

Then set them in your environment:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Multiple Chat IDs
To send alerts to multiple chats, modify the `send_telegram_alert` function:

```python
TELEGRAM_CHAT_IDS = ["123456789", "-1001234567890"]  # Multiple chat IDs

def send_telegram_alert(message: str):
    for chat_id in TELEGRAM_CHAT_IDS:
        # Send to each chat ID
        # ... existing code ...
```

## 📱 Alert Format

Your Telegram alerts will have the same format as Discord alerts:

### Simple Mode:
```
🚨 **BREAKOUT DETECTED** 🚨
**Pair**: `BTC-USD`
**Δ**: `2.34%` | **W**: `1.87%`
**Bands**: FAST, MEDIUM
**Time**: 15:30:45 UTC
```

### Pro Mode:
```
🚨 **BREAKOUT DETECTED** 🚨
**Pair**: `BTC-USD`
**Price**: `$45,678.90`
**Δ**: `2.34%`  |  **W**: `1.87%`
**Candle**: `60s`
• **FAST** (n=10): over max by `1.45%`, vol `1500` vs avg `1200` (x`1.25`), `$68,500/min`
• **MEDIUM** (n=15): over max by `1.78%`, vol `1500` vs avg `900` (x`1.67`), `$68,500/min`
**Time**: 15:30:45 UTC
```

## 🛡️ Security Best Practices

1. **Keep your bot token secret** - never share it publicly
2. **Use environment variables** for production deployments
3. **Regularly rotate tokens** if compromised
4. **Limit bot permissions** to only what's needed
5. **Monitor bot usage** through BotFather analytics

## 📞 Support

If you encounter issues:
1. **Check the console output** for error messages
2. **Verify your bot token and chat ID** are correct
3. **Test manually** by sending a message to your bot
4. **Check Telegram API status** if nothing works

---

🎉 **Congratulations!** You should now be receiving Telegram alerts alongside your Discord notifications for all breakout detections!

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
