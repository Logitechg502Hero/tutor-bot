from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import asyncio

from filters import AdminFilter
from base.visual.markups import admin as admin_markups
import vars


router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class BroadcastStates(StatesGroup):
    choose_target = State()
    input_text = State()
    confirm = State()


_target_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👥 Всем пользователям', callback_data='broadcast_all')],
    [InlineKeyboardButton(text='🧑‍🏫 Только репетиторам', callback_data='broadcast_tutor')],
    [InlineKeyboardButton(text='🎓 Только ученикам', callback_data='broadcast_tutee')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='main')],
])

_cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='main')]
])


@router.callback_query(F.data == 'broadcast')
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastStates.choose_target)
    try:
        await callback.message.edit_text('📢 Выберите аудиторию:', reply_markup=_target_kb)
    except Exception:
        await callback.message.answer('📢 Выберите аудиторию:', reply_markup=_target_kb)
    await callback.answer(show_alert=False)


@router.callback_query(BroadcastStates.choose_target, F.data.startswith('broadcast_'))
async def broadcast_target(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split('_')[1]
    users = await vars.database.get_users_by_role(None if role == 'all' else role)
    await state.update_data(user_ids=[u['user_id'] for u in users])
    count = len(users)
    await state.set_state(BroadcastStates.input_text)
    try:
        await callback.message.edit_text(
            f'Введите текст сообщения.\n\nБудет отправлено: <b>{count} пользователям</b>',
            reply_markup=_cancel_kb,
            parse_mode='HTML'
        )
    except Exception:
        await callback.message.answer(f'Введите текст. Получателей: {count}')
    await callback.answer(show_alert=False)


@router.message(BroadcastStates.input_text, F.text)
async def broadcast_text(message: Message, state: FSMContext):
    data = await state.get_data()
    count = len(data['user_ids'])
    await state.update_data(text=message.text)
    await state.set_state(BroadcastStates.confirm)
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'✅ Отправить {count} пользователям', callback_data='broadcast_confirm')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data='main')],
    ])
    await message.answer(
        f'📢 <b>Превью:</b>\n\n{message.text}\n\n<i>Отправить {count} пользователям?</i>',
        reply_markup=confirm_kb,
        parse_mode='HTML'
    )


@router.callback_query(BroadcastStates.confirm, F.data == 'broadcast_confirm')
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    user_ids = data['user_ids']
    text = data['text']
    sent, failed = 0, 0
    status_msg = await callback.message.answer('⏳ Отправляю...')
    for uid in user_ids:
        try:
            await vars.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await status_msg.edit_text(
        f'✅ Рассылка завершена\n\nОтправлено: {sent}\nОшибок: {failed}',
        reply_markup=admin_markups.main_menu_kb
    )
    await callback.answer(show_alert=False)
