from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from aiogram_dialog import DialogManager, StartMode

from base.handlers.admin.requests_dialogs.states import RequestsStates

from base.visual.markups import admin as admin_markups
from base.visual.markups import user as users_markups

from filters import AdminFilter


router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(Command('start'))
async def start_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Выберите действие', reply_markup=admin_markups.main_kb)


@router.message(Command('user'))
async def users_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Меню', reply_markup=users_markups.main_kb)


@router.callback_query(F.data == 'main')
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer('Выберите действие', reply_markup=admin_markups.main_kb)


@router.callback_query(F.data == 'requests')
async def requests_menu(callback: CallbackQuery, state: FSMContext, dialog_manager: DialogManager):
    await state.clear()
    await callback.answer(show_alert=False)
    await dialog_manager.start(RequestsStates.main, mode=StartMode.RESET_STACK)


@router.message(Command('make_request'))
async def make_request(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Выберите действие', reply_markup=users_markups.put_request_kb)
