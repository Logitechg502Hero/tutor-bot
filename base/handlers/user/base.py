from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from base.states.user import UserStates

from datetime import datetime

from base.visual.markups import user as user_markups
from base.visual.texts import user as user_texts
from utils import user_text as user_text_utils

import vars
import auto_moderator

from logger_config import logger


router = Router()


async def _show_profile(message: Message):
    user = vars.database.get_user(message.from_user.id)
    role = user['role']
    user_data = vars.database.get_tutor_data(message.from_user.id) if role == 'tutor' else vars.database.get_tutee_data(message.from_user.id)
    text = user_text_utils.user_questionnaire_text(user, user_data)
    photo_id = user_data.get('photo_path') if role == 'tutor' else None
    if photo_id:
        await message.answer_photo(photo=photo_id, caption=text, reply_markup=user_markups.profile_kb)
    else:
        await message.answer(text, reply_markup=user_markups.profile_kb)


@router.message(Command('start'))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user = vars.database.get_user(message.from_user.id)
    if not user:
        await message.answer(user_texts.start_text)
        await message.answer(user_texts.input_role_text, reply_markup=user_markups.role_kb)
    else:
        await _show_profile(message)


@router.callback_query(F.data == 'cancel')
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(user_texts.cancel_text, reply_markup=user_markups.main_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'mainMenu')
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(user_texts.main_menu_text, reply_markup=user_markups.main_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'putRequest')
async def put_request_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f'Error deleting message after putRequest: {e}')
    user_id = callback.from_user.id
    user = vars.database.get_user(user_id)
    if user['role'] == 'tutor':
        user_data = vars.database.get_tutor_data(user_id)
    else:
        user_data = vars.database.get_tutee_data(user_id)
    approved, reason, has_link = auto_moderator.moderate(user, user_data, vars.ADMIN_USERNAME)
    if approved:
        vars.database.upsert_request(user_id, datetime.now(), 'approved')
        await callback.message.answer('Заявка принята! Скоро ваша анкета будет опубликована.', reply_markup=user_markups.main_kb)
        logger.info(f'Request auto-approved for user {user_id}')
    elif has_link:
        await state.set_state(UserStates.awaiting_payment_screenshot)
        await callback.message.answer(
            f'В вашей анкете есть ссылка на внешний ресурс.\n\n'
            f'Размещение ссылки стоит <b>300 руб.</b>\n\n'
            f'Переведите на номер <b>+79857770845</b> (Тинькофф)\n'
            f'с комментарием: <code>репетитор {user_id}</code>\n\n'
            f'Затем нажмите кнопку ниже и пришлите скриншот оплаты.',
            reply_markup=user_markups.paid_link_kb,
            parse_mode='HTML'
        )
        logger.info(f'Payment requested from user {user_id} for external link')
    else:
        vars.database.upsert_request(user_id, datetime.now(), 'rejected')
        await callback.message.answer(user_texts.request_rejected_text.format(reason=reason), reply_markup=user_markups.main_kb)
        logger.info(f'Request auto-rejected for user {user_id}: {reason}')
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'paidLink')
async def paid_link_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Пришлите скриншот оплаты:')
    await callback.answer(show_alert=False)


@router.message(UserStates.awaiting_payment_screenshot)
async def payment_screenshot_handler(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer('Пожалуйста, пришлите именно скриншот (фото).')
        return
    await state.clear()
    user_id = message.from_user.id
    username = f'@{message.from_user.username}' if message.from_user.username else str(user_id)
    admins = vars.database.get_admins()
    for admin_id in admins:
        await vars.bot.send_photo(
            admin_id,
            message.photo[-1].file_id,
            caption=f'💳 Скриншот оплаты за ссылку\nПользователь: {username} (ID: {user_id})\n\n'
                    f'Проверьте перевод и одобрите заявку в /start → Заявки'
        )
    vars.database.upsert_request(user_id, datetime.now(), 'pending')
    await message.answer(
        'Скриншот отправлен администратору. Заявка будет рассмотрена в ближайшее время.',
        reply_markup=user_markups.main_kb
    )
    logger.info(f'Payment screenshot received from user {user_id}')


@router.callback_query(F.data == 'paidLinkInfo')
async def paid_link_info_handler(callback: CallbackQuery):
    await callback.message.answer(user_texts.paid_link_info_text, reply_markup=user_markups.main_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'buyPosts')
async def buy_posts_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        user_texts.buy_posts_text.format(admin=vars.ADMIN_USERNAME),
        reply_markup=user_markups.main_kb
    )


@router.message(Command('id'))
async def id_handler(message: Message):
    await message.answer(f'Ваш телеграм ID: {message.from_user.id}')


@router.message(StateFilter(None))
async def any_message_handler(message: Message, state: FSMContext):
    user = vars.database.get_user(message.from_user.id)
    if not user:
        await message.answer(user_texts.start_text)
        await message.answer(user_texts.input_role_text, reply_markup=user_markups.role_kb)
    else:
        await _show_profile(message)
