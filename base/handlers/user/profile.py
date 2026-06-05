from aiogram import Router, F
from aiogram.types import CallbackQuery

from base.visual.markups import user as user_markups
from utils import user_text as user_text_utils

import vars

router = Router()


@router.callback_query(F.data == 'profile')
async def profile_handler(callback: CallbackQuery):
    user = await vars.database.get_user(callback.from_user.id)
    if not user:
        return
    text, photo_id = await user_text_utils.resolve_user_data(callback.from_user.id)
    if photo_id:
        await callback.message.answer_photo(photo=photo_id, caption=text, reply_markup=user_markups.profile_kb)
    else:
        await callback.message.answer(text, reply_markup=user_markups.profile_kb)
    await callback.answer(show_alert=False)
