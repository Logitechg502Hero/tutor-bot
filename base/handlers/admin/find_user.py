from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from base.states.admin import AdminStates
from base.visual.markups import admin as admin_markups
from utils.user_text import get_user_screen
from filters import AdminFilter

import vars


router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.callback_query(F.data == 'findUser')
async def find_user(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.find_user_id)
    await callback.message.answer('Введите ID пользователя', reply_markup=admin_markups.main_menu_kb)


@router.message(AdminStates.find_user_id)
async def find_user_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
    except ValueError:
        await message.answer('ID должен быть числом. Попробуйте ещё раз.', reply_markup=admin_markups.main_menu_kb)
        return
    user = await vars.database.get_user(user_id)
    if not user:
        await message.answer('Пользователь не найден!', reply_markup=admin_markups.main_menu_kb)
        return
    scheduled = await vars.database.get_user_scheduled_posts(user_id)
    pending = [p for p in scheduled if p['status'] == 'pending']
    if pending:
        lines = '\n'.join(datetime.fromisoformat(p['post_date']).strftime('%d.%m.%Y %H:%M') for p in pending)
        await message.answer(f'Запланированные посты:\n{lines}')
    await get_user_screen(user_id, message.chat.id, admin_markups.make_user_kb(user_id))
    await vars.database.add_profile_view(user_id)
    await state.clear()


@router.callback_query(F.data.startswith('viewUser_'))
async def view_user(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    await get_user_screen(user_id, callback.message.chat.id, admin_markups.make_user_kb(user_id))
    await vars.database.add_profile_view(user_id)


@router.callback_query(F.data.startswith('addPost_'))
async def add_post(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split('_')[1])
    await state.update_data(user_id=user_id)
    await state.set_state(AdminStates.add_post_date)
    await callback.message.answer('Введите дату для поста в формате DD.MM.YYYY HH:MM', reply_markup=admin_markups.main_menu_kb)


@router.message(AdminStates.add_post_date)
async def add_post_date(message: Message, state: FSMContext):
    try:
        date = datetime.strptime(message.text, '%d.%m.%Y %H:%M')
    except ValueError:
        await message.answer('Неверный формат даты! Попробуйте снова.', reply_markup=admin_markups.main_menu_kb)
        return
    user_id = (await state.get_data())['user_id']
    await vars.database.add_scheduled_post(user_id, date, 'pending')
    await message.answer('Пост добавлен в очередь!', reply_markup=admin_markups.make_back_kb(f'viewUser_{user_id}'))
    await state.clear()
