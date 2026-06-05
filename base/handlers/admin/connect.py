from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from base.visual.markups import admin as admin_markups

import vars


router = Router()


@router.message(Command('admin'))
async def connect_admin(message: Message, command: CommandObject):

    if command.args == vars.BOT_PASSWORD:
        vars.database.add_admin(message.from_user.id)
        vars.admin_ids.add(message.from_user.id)
        await message.answer('Добро пожаловать!', reply_markup=admin_markups.main_kb)
