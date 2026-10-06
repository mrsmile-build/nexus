"""
Telegram notifier for NEXUS briefings.
"""
import os
import json
import urllib.request

class TelegramNotifier:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    def send(self, message: str, parse_mode: str = "HTML"):
        if not self.token or not self.chat_id:
            return {"sent": False, "error": "Telegram not configured"}

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = json.dumps({
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"sent": True, "response": json.loads(resp.read().decode())}
        except Exception as e:
            return {"sent": False, "error": str(e)}
