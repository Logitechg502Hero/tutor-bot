from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from database import Database
from base.visual.texts import user as user_texts
from base.visual.markups import user as user_markups
from utils import user_text as util_user_text
from logger_config import logger

MSK = ZoneInfo('Europe/Moscow')


class PostScheduler:

    def __init__(self, database: Database, bot: Bot, chat_id: int):
        self._db = database
        self._bot = bot
        self.chat_id = chat_id
        self._admin_id: int | None = None
        self.scheduler = AsyncIOScheduler(timezone=MSK)
        self.scheduler.add_job(self._approved_post_checker, 'cron', hour=12, minute=0)
        self.scheduler.add_job(self._approved_post_checker, 'cron', hour=19, minute=0)
        self.scheduler.add_job(self._check_users_for_new_requests, 'interval', minutes=10)
        self.scheduler.add_job(self._check_scheduled_posts, 'interval', minutes=1, next_run_time=datetime.now())
        self.scheduler.add_job(self._frequent_poster, 'interval', hours=1, next_run_time=datetime.now())
        self.scheduler.add_job(self._unpin_expired, 'interval', hours=1, next_run_time=datetime.now())
        self.scheduler.add_job(self._weekly_stats, 'cron', day_of_week='sun', hour=18, minute=0)
        self.scheduler.start()
        logger.info('Post scheduler initialized and started (timezone: Europe/Moscow)')

    async def _post_anketa_to_channel(self, user_id: int) -> int | None:
        """Публикует анкету в канал, возвращает message_id или None при ошибке."""
        user = await self._db.get_user(user_id)
        if not user:
            return None
        if user['role'] == 'tutor':
            user_data = await self._db.get_tutor_data(user_id)
        else:
            user_data = await self._db.get_tutee_data(user_id)
        rating = await self._db.get_tutor_rating(user_id) if user['role'] == 'tutor' else None
        user_text = util_user_text.user_questionnaire_text(user, user_data, rating)
        photo_id = user_data.get('photo_file_id') if user['role'] == 'tutor' else None
        try:
            if photo_id:
                msg = await self._bot.send_photo(self.chat_id, photo_id, caption=user_text)
            else:
                msg = await self._bot.send_message(self.chat_id, user_text)
            return msg.message_id
        except Exception as e:
            logger.error(f'Error posting anketa for user {user_id}: {e}')
            return None

    async def _pin_message(self, msg_id: int):
        try:
            await self._bot.pin_chat_message(self.chat_id, msg_id, disable_notification=True)
        except TelegramBadRequest as e:
            logger.warning(f'Cannot pin message {msg_id}: {e}')

    async def _unpin_message(self, msg_id: int):
        try:
            await self._bot.unpin_chat_message(self.chat_id, msg_id)
        except TelegramBadRequest as e:
            logger.warning(f'Cannot unpin message {msg_id}: {e}')

    async def _delete_channel_message(self, msg_id: int):
        try:
            await self._bot.delete_message(self.chat_id, msg_id)
        except TelegramBadRequest as e:
            logger.warning(f'Cannot delete channel message {msg_id}: {e}')

    async def _send_one_approved(self) -> str:
        """Берёт первую approved-заявку, публикует, возвращает результат строкой."""
        requests = await self._db.get_requests_by_status(statuses=['approved'])
        if not requests:
            return 'нет одобренных заявок'
        user_id = requests[0]['user_id']
        user = await self._db.get_user(user_id)
        if not user:
            await self._db.upsert_request(user_id, datetime.now(), 'rejected')
            return f'user {user_id} не найден — удалён из очереди'

        msg_id = await self._post_anketa_to_channel(user_id)
        if msg_id is None:
            if self._admin_id:
                await self._bot.send_message(self._admin_id, f'❌ Ошибка публикации анкеты user {user_id}')
            return f'ошибка публикации user {user_id}'

        await self._db.upsert_request(user_id, datetime.now(), 'finished')

        # Сохраняем msg_id для premium-функций
        await self._db.update_channel_msg_id(user_id, msg_id)

        # Если у пользователя активен закреп — пиним
        premium = await self._db.get_premium(user_id)
        if premium and premium.get('pin_until'):
            pin_until = datetime.fromisoformat(premium['pin_until'])
            if pin_until > datetime.now():
                # Откреп старого, если был
                if premium.get('pinned_msg_id'):
                    await self._unpin_message(premium['pinned_msg_id'])
                await self._pin_message(msg_id)
                await self._db.update_pinned_msg_id(user_id, msg_id)

        logger.info(f'Post sent in channel for user {user_id}, msg_id={msg_id}')
        if self._admin_id:
            user_data = await self._db.get_tutor_data(user_id) or await self._db.get_tutee_data(user_id)
            await self._bot.send_message(
                self._admin_id,
                f'✅ Анкета @{(user_data or {}).get("contacts","?")[:30]} опубликована в канале.'
            )
        return f'ok, user {user_id}'

    async def _approved_post_checker(self):
        await self._send_one_approved()

    async def send_want_to_put_request_message(self, user_id: int):
        await self._bot.send_message(
            user_id,
            user_texts.want_to_put_request_text,
            reply_markup=user_markups.put_request_kb
        )

    async def _check_users_for_new_requests(self):
        now = datetime.now()
        requests = await self._db.get_requests_by_status(statuses=['finished', 'rejected'])
        for request in requests:
            user_id = request['user_id']
            # Пользователи с частой публикацией сами не получают напоминание
            premium = await self._db.get_premium(user_id)
            if premium and premium.get('frequent_until'):
                try:
                    freq_until = datetime.fromisoformat(premium['frequent_until'])
                    if freq_until > now:
                        continue
                except Exception:
                    pass
            date = datetime.fromisoformat(request['created_at'])
            if now - date <= timedelta(days=7):
                logger.debug(f'Time since last request: {now - date}')
                continue
            logger.info(f'Sending want_to_put_request message to user {user_id}')
            await self.send_want_to_put_request_message(user_id)

    async def _check_scheduled_posts(self):
        scheduled = await self._db.get_ready_scheduled_posts()
        for post in scheduled:
            try:
                await util_user_text.get_user_screen(post['user_id'], self.chat_id)
                await self._db.update_scheduled_post(post['post_id'], 'finished')
                logger.info(f'Scheduled post {post["post_id"]} sent')
            except Exception as e:
                logger.error(f'Error sending scheduled post {post["post_id"]}: {e}')

    async def _frequent_poster(self):
        """Каждый час проверяет premium-пользователей и публикует анкеты каждые 3 дня."""
        users = await self._db.get_active_frequent_users()
        for row in users:
            user_id = row['user_id']
            try:
                # Удаляем старый пост, если есть
                if row.get('channel_msg_id'):
                    await self._delete_channel_message(row['channel_msg_id'])

                msg_id = await self._post_anketa_to_channel(user_id)
                if msg_id is None:
                    continue

                now = datetime.now()
                await self._db.update_channel_msg_id(user_id, msg_id)
                await self._db.update_frequent_last_post(user_id, now)

                # Если активен закреп — пиним новый, откреп старый
                if row.get('pin_until'):
                    try:
                        pin_until = datetime.fromisoformat(row['pin_until'])
                        if pin_until > now:
                            if row.get('pinned_msg_id'):
                                await self._unpin_message(row['pinned_msg_id'])
                            await self._pin_message(msg_id)
                            await self._db.update_pinned_msg_id(user_id, msg_id)
                    except Exception:
                        pass

                # Обновляем статус заявки чтобы не получал лишние напоминания
                await self._db.upsert_request(user_id, now, 'finished')

                logger.info(f'Frequent post for user {user_id}, msg_id={msg_id}')
                try:
                    await self._bot.send_message(
                        user_id,
                        '🔄 Ваша анкета автоматически опубликована в канале снова!'
                    )
                except Exception:
                    pass
            except Exception as e:
                logger.error(f'Frequent poster error for user {user_id}: {e}')

    async def _unpin_expired(self):
        """Откреп просроченных закреплений."""
        rows = await self._db.get_expired_pins()
        for row in rows:
            user_id = row['user_id']
            try:
                if row.get('pinned_msg_id'):
                    await self._unpin_message(row['pinned_msg_id'])
                await self._db.clear_pin(user_id)
                logger.info(f'Pin expired for user {user_id}')
                try:
                    await self._bot.send_message(
                        user_id,
                        '📌 Закрепление вашей анкеты истекло.\n\n'
                        'Хотите продлить? Нажмите 💎 Продвижение в главном меню.'
                    )
                except Exception:
                    pass
            except Exception as e:
                logger.error(f'Unpin error for user {user_id}: {e}')

    async def _weekly_stats(self):
        tutor_ids = await self._db.get_tutors_with_views()
        for tutor_id in tutor_ids:
            try:
                views = await self._db.get_views_last_7_days(tutor_id)
                avg, cnt = await self._db.get_tutor_rating(tutor_id)
                rating_str = f'⭐️ {avg} ({cnt} отзывов)' if cnt > 0 else 'отзывов пока нет'
                await self._bot.send_message(
                    tutor_id,
                    f'📊 Статистика за неделю\n\n'
                    f'👀 Вашу анкету просмотрели: {views} раз\n'
                    f'⭐️ Ваш рейтинг: {rating_str}\n\n'
                    f'💡 Хотите обновить анкету?',
                    reply_markup=user_markups.change_kb
                )
            except Exception as e:
                logger.error(f'Weekly stats error for tutor {tutor_id}: {e}')
