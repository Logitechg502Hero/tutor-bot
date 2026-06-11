from aiogram import Dispatcher, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram_dialog import setup_dialogs
import asyncio
import time

import vars
from post_scheduler import PostScheduler
from base.handlers.user import router as user_router
from base.handlers.admin import router as admin_router
from dashboard import start_dashboard
from logger_config import logger
from publish_ankety import publisher_task


_START_TS = time.time()
health_router = Router()


@health_router.message(Command('ping'))
async def cmd_ping(message: Message):
    up = int(time.time() - _START_TS)
    h, m, s = up // 3600, (up % 3600) // 60, up % 60
    try:
        st = await vars.database.get_dashboard_stats()
        stats_line = (
            f"Репетиторов: {st.get('tutors', '?')}\n"
            f"Учеников: {st.get('tutees', '?')}\n"
            f"На модерации: {st.get('pending', '?')}\n"
            f"Опубликовано за 7 дней: {st.get('published_7d', '?')}"
        )
    except Exception as e:
        stats_line = f'(статистика недоступна: {e})'
    await message.answer(
        f"✅ Бот жив\nАптайм: {h}ч {m}м {s}с\n\n{stats_line}"
    )


async def main():
    await vars.database.initialize()
    vars.admin_ids = set(await vars.database.get_admins())
    vars.main_loop = asyncio.get_running_loop()
    vars.post_scheduler = PostScheduler(vars.database, vars.bot, vars.CHAT_ID)

    start_dashboard()
    asyncio.create_task(publisher_task())

    dp = Dispatcher()
    dp.message.filter(F.chat.type == ChatType.PRIVATE)
    dp.callback_query.middleware(CallbackAnswerMiddleware(show_alert=False))
    setup_dialogs(dp)
    dp.include_router(health_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await vars.bot.delete_webhook(drop_pending_updates=True)
    logger.info('Bot started')
    await dp.start_polling(vars.bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot stopped')
