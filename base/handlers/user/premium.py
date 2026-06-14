from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from base.states.user import UserStates
from base.visual.markups import user as user_markups
from base.visual.texts import user as user_texts
from logger_config import logger
import vars

router = Router()

PRICES = {
    'frequent': 200,
    'pin': 300,
    'combo': 400,
}

PLAN_LABELS = {
    'frequent': 'Учащённые выходы',
    'pin': 'Закрепление на 7 дней',
    'combo': 'Комбо (выходы + закреп)',
}


async def _edit_or_answer(callback: CallbackQuery, text: str, reply_markup):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode='HTML')


@router.callback_query(F.data == 'premiumMenu')
async def premium_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _edit_or_answer(callback, user_texts.premium_menu_text, user_markups.premium_menu_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data.in_({'buyFrequent', 'buyPin', 'buyCombo'}))
async def buy_plan(callback: CallbackQuery, state: FSMContext):
    plan_map = {'buyFrequent': 'frequent', 'buyPin': 'pin', 'buyCombo': 'combo'}
    plan = plan_map[callback.data]
    amount = PRICES[plan]
    user_id = callback.from_user.id
    await state.update_data(premium_plan=plan)
    await state.set_state(UserStates.awaiting_premium_screenshot)
    text = user_texts.premium_payment_text.format(amount=amount, user_id=user_id)
    await callback.message.answer(text, reply_markup=user_markups.premium_pay_kb, parse_mode='HTML')
    await callback.answer(show_alert=False)


@router.callback_query(F.data == 'sendPremiumScreenshot')
async def prompt_screenshot(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('📸 Пришлите скриншот оплаты:')
    await callback.answer(show_alert=False)


@router.message(UserStates.awaiting_premium_screenshot)
async def receive_premium_screenshot(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer('Пожалуйста, пришлите именно скриншот (фото).')
        return
    data = await state.get_data()
    plan = data.get('premium_plan', 'unknown')
    await state.clear()
    user_id = message.from_user.id
    username = f'@{message.from_user.username}' if message.from_user.username else str(user_id)
    amount = PRICES.get(plan, '?')
    label = PLAN_LABELS.get(plan, plan)
    for admin_id in vars.admin_ids:
        try:
            await vars.bot.send_photo(
                admin_id,
                message.photo[-1].file_id,
                caption=(
                    f'💳 <b>Оплата premium</b>\n'
                    f'Пользователь: {username} (ID: <code>{user_id}</code>)\n'
                    f'Тариф: {label} — {amount} ₽\n\n'
                    f'Активировать: <code>/grant {user_id} {plan} 30</code>'
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f'Error sending premium screenshot to admin {admin_id}: {e}')
    await message.answer(user_texts.premium_waiting_text, reply_markup=user_markups.main_kb)
    logger.info(f'Premium screenshot received from user {user_id}, plan={plan}')


@router.callback_query(F.data == 'myRef')
async def my_ref(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    bot_info = await vars.bot.get_me()
    link = f'https://t.me/{bot_info.username}?start=ref_{user_id}'
    count = await vars.database.get_referral_count(user_id)
    text = user_texts.referral_link_text.format(link=link, count=count)
    try:
        await callback.message.edit_text(text, reply_markup=user_markups.main_kb, parse_mode='HTML')
    except Exception:
        await callback.message.answer(text, reply_markup=user_markups.main_kb, parse_mode='HTML')
    await callback.answer(show_alert=False)
