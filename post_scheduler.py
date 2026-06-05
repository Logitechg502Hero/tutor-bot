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
        self.scheduler.start()
        logger.info('Post scheduler initialized and started')

    async def _approved_post_checker(self):
        now = datetime.now()
        # if now.weekday() in [5, 6]:
        #     return
        requests = self._db.get_requests_by_status(statuses=['approved'])
        if not requests:
            return
        user_id = requests[0]['user_id']
        user = self._db.get_user(user_id)
        role = user['role']
        if role == 'tutor':
            user_data = self._db.get_tutor_data(user_id)
        else:
            user_data = self._db.get_tutee_data(user_id)
        user_text = util_user_text.user_questionnaire_text(user, user_data)
        if user_data.get('photo_path') is None:
            method = self._bot.send_message
            kwargs = {
                'chat_id': self.chat_id,
                'text': user_text
            }
        else:
            method = self._bot.send_photo
            kwargs = {
                'chat_id': self.chat_id,
                'photo': user_data.get('photo_path'),
                'caption': user_text
            }
        try:
            await method(**kwargs)
            self._db.upsert_request(user_id, datetime.now(), 'finished')
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
        requests = self._db.get_requests_by_status(statuses=['finished', 'rejected'])
        for request in requests:
            date = datetime.fromisoformat(request['created_at'])
            if now - date <= timedelta(days=7):
                logger.debug(f'Time since last request: {now - date}')
                continue
            logger.info(f'Sending want_to_put_request message to user {request["user_id"]}')
            await self.send_want_to_put_request_message(request['user_id'])

    async def _check_scheduled_posts(self):
        scheduled = self._db.get_ready_scheduled_posts()
        for post in scheduled:
            try:
                await util_user_text.get_user_screen(
                    post['user_id'],
                    self.chat_id
                )
                self._db.update_scheduled_post(post['post_id'], 'finished')
                logger.info(f'Scheduled post {post["post_id"]} sent')
            except Exception as e:
                logger.error(f'Error sending scheduled post {post["post_id"]}: {e}')
                continue
