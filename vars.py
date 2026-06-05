from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
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
CHAT_ID = int(os.getenv('chat_id'))

database = Database()

properties = DefaultBotProperties(parse_mode='HTML')
bot = Bot(BOT_TOKEN, default=properties)

admin_ids: set[int] = set()
post_scheduler = None   # set in main() after event loop starts
main_loop = None        # set in main() for dashboard thread
