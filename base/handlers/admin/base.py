from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, StartMode

from base.handlers.admin.requests_dialogs.states import RequestsStates
from base.visual.markups import admin as admin_markups
from base.visual.markups import user as user_markups
from filters import AdminFilter

import vars


router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


async def _admin_menu_text() -> str:
    stats = await vars.database.get_dashboard_stats()
    return (
        f'📊 <b>Панель управления</b>\n\n'
        f'🧑‍🏫 Репетиторов: <b>{stats["tutors"]}</b>\n'
        f'👨‍🎓 Учеников: <b>{stats["tutees"]}</b>\n'
        f'⏳ На модерации: <b>{stats["pending"]}</b>\n'
        f'✅ Опубликовано за 7 дней: <b>{stats["published_7d"]}</b>'
    )


async def _edit_or_answer_admin(callback: CallbackQuery, text: str, kb):
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode='HTML')
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode='HTML')


@router.message(Command('start'))
async def start_admin(message: Message, state: FSMContext):
    await state.clear()
    text = await _admin_menu_text()
    await message.answer(text, reply_markup=admin_markups.main_kb, parse_mode='HTML')


@router.message(Command('user'))
async def users_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('👤 Режим пользователя', reply_markup=user_markups.main_with_admin_kb)


@router.callback_query(F.data == 'main')
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = await _admin_menu_text()
    await _edit_or_answer_admin(callback, text, admin_markups.main_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'requests')
async def requests_menu(callback: CallbackQuery, state: FSMContext, dialog_manager: DialogManager):
    await state.clear()
    await callback.answer(show_alert=False)
    await dialog_manager.start(RequestsStates.main, mode=StartMode.RESET_STACK)


@router.callback_query(F.data == 'userMode')
async def user_mode(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text('👤 Режим пользователя', reply_markup=user_markups.main_with_admin_kb)
    except Exception:
        await callback.message.answer('👤 Режим пользователя', reply_markup=user_markups.main_with_admin_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'adminPanel')
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = await _admin_menu_text()
    await _edit_or_answer_admin(callback, text, admin_markups.main_kb)
    await callback.answer(show_alert=False)


@router.message(Command('make_request'))
async def make_request(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Выберите действие', reply_markup=user_markups.put_request_kb)
