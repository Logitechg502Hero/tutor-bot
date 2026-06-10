import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
SOURCE_CHAT_ID = -4712837022
TARGET_CHANNEL = "@repetitor_msc"
QUEUE_FILE = "ankety_queue.json"
NOTICE = "\n\n📌 Анкета из архива. Актуальность уточните напрямую у автора."
MSK = timezone(timedelta(hours=3))
PUBLISH_HOURS = {12, 19}


async def build_queue(client):
    print("Загружаю анкеты из группы...")
    messages = []
    async for msg in client.iter_messages(SOURCE_CHAT_ID, limit=500):
        if msg.text and len(msg.text.strip()) > 50:
            messages.append({"id": msg.id, "text": msg.text, "published": False})
    messages.reverse()
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    print(f"Загружено {len(messages)} анкет в {QUEUE_FILE}")
    return messages


def load_queue():
    with open(QUEUE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


async def publish_next(client, queue):
    for i, item in enumerate(queue):
        if not item["published"]:
            await client.send_message(TARGET_CHANNEL, item["text"] + NOTICE)
            queue[i]["published"] = True
            save_queue(queue)
            remaining = sum(1 for x in queue if not x["published"])
            print(f"Опубликована анкета #{i+1}. Осталось: {remaining}")
            return True
    print("Очередь пуста — все анкеты опубликованы.")
    return False


async def main():
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        if not os.path.exists(QUEUE_FILE):
            queue = await build_queue(client)
        else:
            queue = load_queue()
            remaining = sum(1 for x in queue if not x["published"])
            print(f"Очередь загружена. Осталось опубликовать: {remaining}")

        last_published_hour = None

        while True:
            now = datetime.now(MSK)
            hour = now.hour

            if hour in PUBLISH_HOURS and last_published_hour != hour:
                print(f"[{now.strftime('%H:%M')} МСК] Публикую анкету...")
                published = await publish_next(client, queue)
                if published:
                    last_published_hour = hour
                else:
                    break

            await asyncio.sleep(30)


asyncio.run(main())
