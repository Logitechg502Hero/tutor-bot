from loguru import logger
import sys
import os
import asyncio
import aiohttp


ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
BOT_TOKEN = os.getenv('bot_token')


async def _send_tg_error(message: str):
    if not ADMIN_CHAT_ID or not BOT_TOKEN:
        return
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={
                'chat_id': ADMIN_CHAT_ID,
                'text': f'🔴 <b>Ошибка бота:</b>\n<pre>{message[:3000]}</pre>',
                'parse_mode': 'HTML'
            })
    except Exception:
        pass


def _tg_error_sink(message):
    record = message.record
    if record['level'].name == 'ERROR':
        text = f"{record['file']}:{record['line']} | {record['message']}"
        if record.get('exception'):
            import traceback
            text += '\n' + ''.join(traceback.format_exception(*record['exception']))
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_send_tg_error(text))
        except Exception:
            pass


logger.remove(0)

logger.add(
    sink=sys.stdout,
    level='DEBUG',
    format='<level><b>{level}</b></level> | '
           '<g>{time:%d.%m.%Y %H:%M:%S}</g> | '
           '<m>{file}</m>:<m>{function}</m>:<m>{line}</m> | '
           '<level><b>{message}</b></level>'
)

logger.add(
    sink=_tg_error_sink,
    level='ERROR',
    format='{message}'
)

logger.level('ERROR', color='<r>')
logger.level('DEBUG', color='<c>')
logger.level('INFO', color='<g>')
