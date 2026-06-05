from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from datetime import datetime

from base.states.user import UserStates
from base.visual.markups import user as user_markups
from base.visual.texts import user as user_texts
from utils import user_text as user_text_utils

import vars
import auto_moderator
from logger_config import logger


router = Router()

CANCEL_WORDS = {'отмена', '❌ отмена', '❌отмена', '/cancel', 'cancel'}


async def _main_menu_text(user_id: int) -> str:
    user = await vars.database.get_user(user_id)
    if user:
        role = user['role']
        data = await vars.database.get_tutor_data(user_id) if role == 'tutor' else await vars.database.get_tutee_data(user_id)
        name = data.get('name') if data else None
        if name:
            return user_texts.main_menu_text.format(name=name)
    return user_texts.main_menu_text_default


async def _edit_or_answer(callback: CallbackQuery, text: str, reply_markup):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)


@router.message(lambda m: m.text and m.text.lower().strip() in CANCEL_WORDS)
async def cancel_text_handler(message: Message, state: FSMContext):
    if await state.get_state() is None:
        return
    await state.clear()
    text = await _main_menu_text(message.from_user.id)
    await message.answer(text, reply_markup=user_markups.main_kb)


@router.message(Command('start'))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user = await vars.database.get_user(message.from_user.id)
    if not user:
        await message.answer(user_texts.start_text, parse_mode='HTML')
        await message.answer(user_texts.input_role_text, reply_markup=user_markups.role_kb)
    else:
        text = await _main_menu_text(message.from_user.id)
        await message.answer(text, reply_markup=user_markups.main_kb)


@router.callback_query(F.data == 'cancel')
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = await _main_menu_text(callback.from_user.id)
    await _edit_or_answer(callback, text, user_markups.main_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'mainMenu')
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = await _main_menu_text(callback.from_user.id)
    await _edit_or_answer(callback, text, user_markups.main_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'putRequest')
async def put_request_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await vars.database.get_user(user_id)
    if user['role'] == 'tutor':
        user_data = await vars.database.get_tutor_data(user_id)
    else:
        user_data = await vars.database.get_tutee_data(user_id)
    approved, reason, has_link = auto_moderator.moderate(user, user_data, vars.ADMIN_USERNAME)
    if not approved and not has_link:
        await callback.message.answer(user_texts.request_rejected_text.format(reason=reason), reply_markup=user_markups.main_kb)
        logger.info(f'Request rejected for user {user_id}: {reason}')
        await callback.answer(show_alert=False)
        return
    rating = await vars.database.get_tutor_rating(user_id) if user['role'] == 'tutor' else None
    preview_text = user_text_utils.user_questionnaire_text(user, user_data, rating)
    await state.update_data(approved=approved, has_link=has_link)
    await state.set_state(UserStates.confirm_request)
    await callback.message.answer(
        f'Так будет выглядеть ваша анкета в канале:\n\n{preview_text}\n\nПодтвердить публикацию?',
        reply_markup=user_markups.confirm_request_kb
    )
    await callback.answer(show_alert=False)


@router.callback_query(UserStates.confirm_request, F.data == 'confirmRequest')
async def confirm_request_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    await state.clear()
    if data.get('has_link'):
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
        logger.info(f'Payment requested from user {user_id}')
    else:
        await vars.database.upsert_request(user_id, datetime.now(), 'approved')
        await callback.message.answer('Заявка принята! Скоро ваша анкета будет опубликована.', reply_markup=user_markups.main_kb)
        logger.info(f'Request approved for user {user_id}')
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
    for admin_id in vars.admin_ids:
        await vars.bot.send_photo(
            admin_id,
            message.photo[-1].file_id,
            caption=f'💳 Скриншот оплаты за ссылку\nПользователь: {username} (ID: {user_id})\n\nПроверьте перевод и одобрите заявку в /start → Заявки'
        )
    await vars.database.upsert_request(user_id, datetime.now(), 'pending')
    await message.answer('Скриншот отправлен администратору. Заявка будет рассмотрена в ближайшее время.', reply_markup=user_markups.main_kb)
    logger.info(f'Payment screenshot received from user {user_id}')


@router.callback_query(F.data == 'buyPosts')
async def buy_posts_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = user_texts.buy_posts_text.format(admin=vars.ADMIN_USERNAME)
    await _edit_or_answer(callback, text, user_markups.main_kb)
    await callback.answer(show_alert=False)


@router.message(Command('id'))
async def id_handler(message: Message):
    await message.answer(f'Ваш телеграм ID: {message.from_user.id}')


@router.message(StateFilter(None))
async def any_message_handler(message: Message, state: FSMContext):
    user = await vars.database.get_user(message.from_user.id)
    if not user:
        await message.answer(user_texts.start_text, parse_mode='HTML')
        await message.answer(user_texts.input_role_text, reply_markup=user_markups.role_kb)
    else:
        text = await _main_menu_text(message.from_user.id)
        await message.answer(text, reply_markup=user_markups.main_kb)
