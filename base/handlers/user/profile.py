from aiogram import Router, F
from aiogram.types import CallbackQuery

from base.visual.texts import user as user_texts
from base.visual.markups import user as user_markups

from utils import user_text as user_text_utils

import vars

router = Router()


@router.callback_query(F.data == 'profile')
async def profile_handler(callback: CallbackQuery):
    user = vars.database.get_user(callback.from_user.id)
    if not user:
        return
    role = user['role']
    if role == 'tutor':
        user_data = vars.database.get_tutor_data(callback.from_user.id)
    else:
        user_data = vars.database.get_tutee_data(callback.from_user.id)
    user_text = user_text_utils.user_questionnaire_text(user, user_data)
    photo_id = user_data.get('photo_path') if role == 'tutor' else None
    if photo_id:
        await callback.message.answer_photo(
            photo=photo_id,
            caption=user_text,
            reply_markup=user_markups.profile_kb
        )
    else:
        await callback.message.answer(user_text, reply_markup=user_markups.profile_kb)
    await callback.answer(show_alert=False)
