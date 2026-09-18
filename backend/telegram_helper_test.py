from telegram import send_telegram_message


success = send_telegram_message(
    "5607150101",
    "🚛 Adama Smart City\n\n"
    "🔔 Notification service test\n"
    "BIN-001 is ready for monitoring."
)

print("Success:", success)