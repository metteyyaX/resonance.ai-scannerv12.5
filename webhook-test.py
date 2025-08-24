import requests, os
url = os.getenv("DISCORD_WEBHOOK_URL")
requests.post(url, json={"content": "✅ Webhook test message"})