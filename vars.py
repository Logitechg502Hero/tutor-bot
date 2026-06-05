from dotenv import load_dotenv

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from post_scheduler import PostScheduler

from database import Database

import os
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


load_dotenv()


BOT_TOKEN = os.getenv('bot_token')
BOT_PASSWORD = os.getenv('bot_password')
ADMIN_USERNAME = os.getenv('admin_username')

database = Database()

properties = DefaultBotProperties(parse_mode='HTML')
bot = Bot(BOT_TOKEN, default=properties)

CHAT_ID = int(os.getenv('chat_id'))

admin_ids: set[int] = set(database.get_admins())

post_scheduler = PostScheduler(database, bot, CHAT_ID)
