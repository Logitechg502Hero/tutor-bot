from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

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
    elif role == 'tutee':
        user_data = vars.database.get_tutee_data(callback.from_user.id)
    user_text = user_text_utils.user_questionnaire_text(user, user_data)
    if role == 'tutor':
        photo_path = user_data['photo_path']
    elif role == 'tutee':
        photo_path = None
    if photo_path:
        await callback.message.answer_photo(
            photo=FSInputFile(photo_path), 
            caption=user_text,
            reply_markup=user_markups.change_kb
        )
    else:
        await callback.message.answer(
            user_text,
            reply_markup=user_markups.change_kb
        )
    await callback.answer(show_alert=False)
