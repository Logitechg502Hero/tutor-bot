from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = 37640634
API_HASH = "64db58c60b6d403ce196342906e462cb"

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    session_str = client.session.save()
    print("\n✅ СТРОКА СЕССИИ (скопируй всё целиком):\n")
    print(session_str)
    print("\nДобавь её в Railway Variables как SESSION_STRING")
