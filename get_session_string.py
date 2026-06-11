from telethon.sync import TelegramClient

API_ID = 37640634
API_HASH = "64db58c60b6d403ce196342906e462cb"

with TelegramClient("session_monitor", API_ID, API_HASH) as client:
    print("\nСТРОКА СЕССИИ (скопируй всё целиком):\n")
    print(client.session.save())
    print()
