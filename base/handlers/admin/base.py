from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, StartMode
from datetime import datetime, timedelta

from base.handlers.admin.requests_dialogs.states import RequestsStates
from base.visual.markups import admin as admin_markups
from base.visual.markups import user as user_markups
from filters import AdminFilter
from logger_config import logger

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


@router.message(Command('grant'))
async def grant_premium(message: Message):
    """
    /grant <user_id> <plan> <days>
    plan: frequent | pin | combo
    Пример: /grant 123456 combo 30
    """
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer('Использование: /grant <user_id> <план> <дней>\nПланы: frequent, pin, combo')
        return
    try:
        user_id = int(parts[1])
        plan = parts[2].lower()
        days = int(parts[3])
    except ValueError:
        await message.answer('Неверный формат. Пример: /grant 123456 combo 30')
        return
    if plan not in ('frequent', 'pin', 'combo'):
        await message.answer('Неверный план. Доступны: frequent, pin, combo')
        return

    until = datetime.now() + timedelta(days=days)
    activated = []
    if plan in ('frequent', 'combo'):
        await vars.database.set_frequent(user_id, until)
        activated.append(f'🔄 Учащённые выходы до {until.strftime("%d.%m.%Y")}')
    if plan in ('pin', 'combo'):
        await vars.database.set_pin(user_id, until)
        activated.append(f'📌 Закрепление до {until.strftime("%d.%m.%Y")}')

    summary = '\n'.join(activated)
    await message.answer(f'✅ Premium активирован для <code>{user_id}</code>:\n{summary}', parse_mode='HTML')
    logger.info(f'Admin granted premium {plan} for {days}d to user {user_id}')

    # Уведомляем пользователя
    try:
        if plan == 'frequent':
            text = f'🎉 <b>Учащённые выходы активированы!</b>\n\nВаша анкета будет публиковаться раз в 3 дня до {until.strftime("%d.%m.%Y")}.'
        elif plan == 'pin':
            text = f'🎉 <b>Закрепление активировано!</b>\n\nВаша анкета закреплена в канале до {until.strftime("%d.%m.%Y")}.'
        else:
            text = (
                f'🎉 <b>Комбо активировано!</b>\n\n'
                f'🔄 Учащённые выходы (раз в 3 дня) до {until.strftime("%d.%m.%Y")}\n'
                f'📌 Закрепление в канале до {until.strftime("%d.%m.%Y")}'
            )
        await vars.bot.send_message(user_id, text, parse_mode='HTML')
    except Exception as e:
        await message.answer(f'⚠️ Не удалось уведомить пользователя: {e}')
