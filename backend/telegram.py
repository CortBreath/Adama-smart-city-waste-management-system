import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def send_telegram_message(chat_id: str, message: str) -> bool:
    """
    Send a message through the Telegram Bot API.

    Returns True when Telegram accepts the message.
    Retries up to 3 times when a temporary network error occurs.
    """

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Telegram error: TELEGRAM_BOT_TOKEN is not configured.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for attempt in range(3):
        try:
            response = httpx.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            if data.get("ok"):
                print(f"Telegram message sent to {chat_id}")
                return True

            print(f"Telegram API error: {data}")
            return False

        except Exception as exc:
            print(
                f"Telegram send failed "
                f"(attempt {attempt + 1}/3): {exc}"
            )

            # Wait before retrying, but don't wait after the final attempt.
            if attempt < 2:
                time.sleep(2)

    print("Telegram notification failed after 3 attempts.")
    return False