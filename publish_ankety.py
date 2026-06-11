import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from logger_config import logger

SOURCE_CHAT_ID = -4712837022
TARGET_CHANNEL = "@repetitor_msc"
QUEUE_FILE = os.path.join(os.getenv('DATA_DIR', '.'), "ankety_queue.json")
NOTICE = "\n\n📌 Анкета из архива. Актуальность уточните напрямую у автора."
MSK = timezone(timedelta(hours=3))
PUBLISH_HOURS = {12, 19}

_client = None  # Telethon-клиент, инициализируется при старте


async def _get_client():
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    global _client
    if _client is None:
        API_ID = int(os.environ["TG_API_ID"])
        API_HASH = os.environ["TG_API_HASH"]
        SESSION_STRING = os.environ["SESSION_STRING"]
        _client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await _client.connect()
    return _client


async def _build_queue() -> list:
    client = await _get_client()
    logger.info('[publisher] загружаю анкеты из архивной группы...')
    messages = []
    async for msg in client.iter_messages(SOURCE_CHAT_ID, limit=500):
        if msg.text and len(msg.text.strip()) > 50:
            messages.append({"id": msg.id, "text": msg.text, "published": False})
    messages.reverse()
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    logger.info(f'[publisher] загружено {len(messages)} анкет')
    return messages


def _load_queue() -> list:
    with open(QUEUE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_queue(queue: list):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


async def _get_queue() -> list:
    if not os.path.exists(QUEUE_FILE):
        return await _build_queue()
    return _load_queue()


async def publish_one_now() -> str:
    """Публикует следующую неопубликованную анкету. Возвращает строку с результатом."""
    try:
        client = await _get_client()
        queue = await _get_queue()
        remaining = sum(1 for x in queue if not x["published"])
        if remaining == 0:
            return 'очередь пуста — все анкеты опубликованы'
        for i, item in enumerate(queue):
            if not item["published"]:
                await client.send_message(TARGET_CHANNEL, item["text"] + NOTICE)
                queue[i]["published"] = True
                _save_queue(queue)
                left = remaining - 1
                logger.info(f'[publisher] анкета #{i+1} опубликована, осталось {left}')
                return f'✅ Анкета #{i+1} опубликована. Осталось: {left}'
    except Exception as e:
        logger.error(f'[publisher] ошибка публикации: {e}')
        return f'❌ Ошибка: {e}'


async def publisher_task():
    if not all(os.getenv(k) for k in ('TG_API_ID', 'TG_API_HASH', 'SESSION_STRING')):
        logger.warning('[publisher] TG_API_ID/TG_API_HASH/SESSION_STRING не заданы — выключен')
        return

    # Импортируем vars здесь, чтобы не было кругового импорта
    import vars

    async def notify(text: str):
        if vars.admin_ids:
            for admin_id in vars.admin_ids:
                try:
                    await vars.bot.send_message(admin_id, text)
                except Exception:
                    pass

    try:
        client = await _get_client()
        queue = await _get_queue()
        remaining = sum(1 for x in queue if not x["published"])
        logger.info(f'[publisher] запущен, в очереди {remaining} анкет')
        await notify(f'📚 Архивный публикатор запущен. В очереди: {remaining} анкет.\nПостит в 12:00 и 19:00 МСК.')
    except Exception as e:
        logger.error(f'[publisher] ошибка при старте: {e}')
        await asyncio.sleep(5)  # vars.admin_ids может ещё не быть
        import vars as v
        for admin_id in v.admin_ids:
            try:
                await v.bot.send_message(admin_id, f'❌ Архивный публикатор не запустился:\n{e}')
            except Exception:
                pass
        return

    last_published_hour = None
    while True:
        try:
            now = datetime.now(MSK)
            hour = now.hour
            if hour in PUBLISH_HOURS and last_published_hour != hour:
                logger.info(f'[publisher] {now.strftime("%H:%M")} МСК — публикую анкету')
                result = await publish_one_now()
                await notify(f'📬 Автопостинг анкет:\n{result}')
                last_published_hour = hour
                if 'очередь пуста' in result:
                    logger.info('[publisher] все анкеты опубликованы, завершаю')
                    break
        except Exception as e:
            logger.error(f'[publisher] ошибка в цикле: {e}')
            await notify(f'❌ Ошибка в публикаторе:\n{e}')
        await asyncio.sleep(30)
