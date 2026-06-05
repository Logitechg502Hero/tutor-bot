from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from datetime import datetime

import utils.validate as validate
import utils.split as split

from base.states.user import UserStates
from base.visual.texts import user as user_texts
from base.visual.markups import user as user_markups

import vars


router = Router()


@router.callback_query(F.data == 'change')
async def change_menu_handler(callback: CallbackQuery, state: FSMContext):
    user = await vars.database.get_user(callback.from_user.id)
    kb = user_markups.make_change_kb(user['role'] == 'tutor')
    try:
        await callback.message.edit_text(user_texts.change_menu_text, reply_markup=kb)
    except Exception:
        await callback.message.answer(user_texts.change_menu_text, reply_markup=kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data.startswith('change/'))
async def change_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(field=callback.data.split('/')[-1])
    await callback.message.answer(user_texts.input_field_text, reply_markup=user_markups.cancel_kb)
    await state.set_state(UserStates.change_value)
    await callback.answer(show_alert=False)


@router.message(UserStates.change_value)
async def change_value_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']

    if field != 'photo_file_id' and message.text is None:
        return
    if field == 'photo_file_id' and message.photo is None:
        return

    value = message.text
    validate_status = True
    error_text = None

    match field:
        case 'age':
            validate_status = validate.validate_age(value)
            error_text = user_texts.invalid_age_text
        case 'experience':
            validate_status = validate.validate_experience(value)
            error_text = user_texts.invalid_experience_text
        case 'info':
            validate_status = validate.validate_info(value)
            error_text = user_texts.invalid_info_text
        case 'price':
            validate_status = validate.validate_price(value)
            error_text = user_texts.invalid_price_text

    if not validate_status:
        await message.answer(error_text)
        return

    user = await vars.database.get_user(message.from_user.id)
    role = user['role']

    if field == 'subject':
        value = ', '.join(split.split_subject(value))
    if field == 'photo_file_id':
        value = message.photo[-1].file_id

    user_id = message.from_user.id
    await vars.database.update_user(user_id, field, value, role)

    repost = False
    for status in ('finished', 'approved'):
        if await vars.database.get_request(user_id, status):
            await vars.database.upsert_request(user_id, datetime.now(), 'pending')
            repost = True
            break

    if repost:
        await message.answer('Профиль обновлён. Заявка отправлена на повторную публикацию.', reply_markup=user_markups.main_kb)
    else:
        await message.answer(user_texts.change_success_text, reply_markup=user_markups.main_kb)
    await state.clear()
