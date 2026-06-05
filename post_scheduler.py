from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from aiogram import Bot
from database import Database
from base.visual.texts import user as user_texts
from base.visual.markups import user as user_markups
from utils import user_text as util_user_text
from logger_config import logger


class PostScheduler:

    def __init__(self, database: Database, bot: Bot, chat_id: int):
        self._db = database
        self._bot = bot
        self.chat_id = chat_id
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self._approved_post_checker, 'cron', hour=12, minute=0)
        self.scheduler.add_job(self._approved_post_checker, 'cron', hour=19, minute=0)
        self.scheduler.add_job(self._check_users_for_new_requests, 'interval', minutes=10)
        self.scheduler.add_job(self._check_scheduled_posts, 'interval', minutes=1, next_run_time=datetime.now())
        self.scheduler.add_job(self._weekly_stats, 'cron', day_of_week='sun', hour=18, minute=0)
        self.scheduler.start()
        logger.info('Post scheduler initialized and started')

    async def _approved_post_checker(self):
        requests = await self._db.get_requests_by_status(statuses=['approved'])
        if not requests:
            return
        user_id = requests[0]['user_id']
        user = await self._db.get_user(user_id)
        if user['role'] == 'tutor':
            user_data = await self._db.get_tutor_data(user_id)
        else:
            user_data = await self._db.get_tutee_data(user_id)
        rating = await self._db.get_tutor_rating(user_id) if user['role'] == 'tutor' else None
        user_text = util_user_text.user_questionnaire_text(user, user_data, rating)
        photo_id = user_data.get('photo_file_id') if user['role'] == 'tutor' else None
        try:
            if photo_id:
                await self._bot.send_photo(self.chat_id, photo_id, caption=user_text)
            else:
                await self._bot.send_message(self.chat_id, user_text)
            await self._db.upsert_request(user_id, datetime.now(), 'finished')
            logger.info(f'Post sent in chat for user {user_id}')
        except Exception as e:
            logger.error(f'Error sending post for user {user_id}: {e}')

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
            date = datetime.fromisoformat(request['created_at'])
            if now - date <= timedelta(days=7):
                logger.debug(f'Time since last request: {now - date}')
                continue
            logger.info(f'Sending want_to_put_request message to user {request["user_id"]}')
            await self.send_want_to_put_request_message(request['user_id'])

    async def _check_scheduled_posts(self):
        scheduled = await self._db.get_ready_scheduled_posts()
        for post in scheduled:
            try:
                await util_user_text.get_user_screen(post['user_id'], self.chat_id)
                await self._db.update_scheduled_post(post['post_id'], 'finished')
                logger.info(f'Scheduled post {post["post_id"]} sent')
            except Exception as e:
                logger.error(f'Error sending scheduled post {post["post_id"]}: {e}')

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
