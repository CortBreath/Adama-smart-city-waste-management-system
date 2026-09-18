import os
import httpx
from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = "5607150101"


if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is missing from backend/.env"
    )


url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


message = (
    "🚛 Adama Smart City\n\n"
    "✅ Telegram notification test successful!\n\n"
    "BIN-001 notification system is ready."
)


response = httpx.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": message,
    },
    timeout=10,
)


print("Status:", response.status_code)
print("Response:", response.json())