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


@health_router.message(Command('dbstatus'))
async def cmd_dbstatus(message: Message):
    """Показывает состояние заявок в БД — сколько pending/approved/finished."""
    try:
        from database import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            rows = {}
            for s in ('pending', 'approved', 'finished', 'rejected'):
                cur = await db.execute("SELECT COUNT(*) FROM requests WHERE status=?", (s,))
                rows[s] = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM users")
            total_users = (await cur.fetchone())[0]
        await message.answer(
            f"📊 <b>Состояние БД</b>\n\n"
            f"Пользователей: {total_users}\n"
            f"Ожидают модерации: {rows['pending']}\n"
            f"Одобрено (в очереди): {rows['approved']}\n"
            f"Опубликовано всего: {rows['finished']}\n"
            f"Отклонено: {rows['rejected']}",
            parse_mode='HTML'
        )
    except Exception as e:
        await message.answer(f'Ошибка: {e}')


@health_router.message(Command('sendnow'))
async def cmd_sendnow(message: Message):
    """Принудительно публикует следующую одобренную анкету прямо сейчас."""
    if vars.post_scheduler is None:
        await message.answer('Scheduler ещё не инициализирован.')
        return
    await message.answer('⏳ Публикую следующую одобренную анкету...')
    result = await vars.post_scheduler._send_one_approved()
    await message.answer(f'Результат: {result}')


async def main():
    await vars.database.initialize()
    vars.admin_ids = set(await vars.database.get_admins())
    vars.main_loop = asyncio.get_running_loop()
    vars.post_scheduler = PostScheduler(vars.database, vars.bot, vars.CHAT_ID)

    # Сообщаем о старте всем admin-ам (помогает понять, что бот перезапустился)
    for admin_id in vars.admin_ids:
        try:
            await vars.bot.send_message(
                admin_id,
                '🟢 <b>Бот запущен</b>\n\n'
                'Команды диагностики:\n'
                '/ping — аптайм + статистика\n'
                '/dbstatus — состояние заявок в БД\n'
                '/sendnow — опубликовать следующую анкету прямо сейчас',
                parse_mode='HTML'
            )
            vars.post_scheduler._admin_id = admin_id  # последний admin получает уведомления
        except Exception:
            pass

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
