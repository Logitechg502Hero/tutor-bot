from aiogram import Dispatcher, F
from aiogram.enums import ChatType
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram_dialog import setup_dialogs
import asyncio

import vars
from post_scheduler import PostScheduler
from base.handlers.user import router as user_router
from base.handlers.admin import router as admin_router
from dashboard import start_dashboard
from logger_config import logger


async def main():
    await vars.database.initialize()
    vars.admin_ids = set(await vars.database.get_admins())
    vars.main_loop = asyncio.get_event_loop()
    vars.post_scheduler = PostScheduler(vars.database, vars.bot, vars.CHAT_ID)

    start_dashboard()

    dp = Dispatcher()
    dp.message.filter(F.chat.type == ChatType.PRIVATE)
    dp.callback_query.middleware(CallbackAnswerMiddleware(show_alert=False))
    setup_dialogs(dp)
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
