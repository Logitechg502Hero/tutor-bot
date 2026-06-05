from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from base.states.user import UserStates
from base.visual.texts import user as user_texts
from base.visual.markups import user as user_markups
from utils import validate, split

import vars


router = Router()
p = user_texts.progress_tutee


@router.callback_query(F.data == 'student')
async def input_role_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(user_texts.tutee_onboarding_text)
    await callback.message.answer(p['name'] + user_texts.input_name_text, reply_markup=user_markups.cancel_kb, parse_mode='HTML')
    await state.set_state(UserStates.tutee_input_name)
    await callback.answer(show_alert=False)


@router.message(UserStates.tutee_input_name, F.text)
async def input_name_handler(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(p['age'] + user_texts.tutee_input_age, reply_markup=user_markups.cancel_kb, parse_mode='HTML')
    await state.set_state(UserStates.tutee_input_age)


@router.message(UserStates.tutee_input_age, F.text)
async def input_age_handler(message: Message, state: FSMContext):
    if not validate.validate_age(message.text, min_age=6):
        await message.answer(user_texts.invalid_age_text)
        return
    await state.update_data(age=int(message.text))
    await message.answer(p['subject'] + user_texts.tutee_input_subject, reply_markup=user_markups.cancel_kb, parse_mode='HTML')
    await state.set_state(UserStates.tutee_input_subject)


@router.message(UserStates.tutee_input_subject, F.text)
async def input_subject_handler(message: Message, state: FSMContext):
    subject = ', '.join(split.split_subject(message.text))
    await state.update_data(subject=subject)
    await message.answer(p['place'] + user_texts.tutee_input_place, reply_markup=user_markups.cancel_kb, parse_mode='HTML')
    await state.set_state(UserStates.tutee_input_place)


@router.message(UserStates.tutee_input_place, F.text)
async def input_place_handler(message: Message, state: FSMContext):
    await state.update_data(place=message.text)
    await message.answer(p['target'] + user_texts.tutee_input_target, reply_markup=user_markups.cancel_kb, parse_mode='HTML')
    await state.set_state(UserStates.tutee_input_target)


@router.message(UserStates.tutee_input_target, F.text)
async def input_target_handler(message: Message, state: FSMContext):
    await state.update_data(target=message.text)
    await message.answer(p['price'] + user_texts.tutee_input_price, reply_markup=user_markups.cancel_kb, parse_mode='HTML')
    await state.set_state(UserStates.tutee_input_price)


@router.message(UserStates.tutee_input_price, F.text)
async def input_price_handler(message: Message, state: FSMContext):
    if not validate.validate_price(message.text):
        await message.answer(user_texts.invalid_price_text)
        return
    await state.update_data(price=float(message.text))
    await message.answer(user_texts.input_contacts_text, reply_markup=user_markups.cancel_kb, parse_mode='HTML')
    await state.set_state(UserStates.tutee_input_contacts)


@router.message(UserStates.tutee_input_contacts, F.text)
async def input_contacts_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await vars.database.create_user(
        user_id=message.from_user.id,
        role='tutee',
        name=data['name'],
        age=data['age'],
        subject=data['subject'],
        place=data['place'],
        target=data['target'],
        contacts=message.text,
        price=data['price']
    )
    await message.answer(user_texts.questionnaire_filled_text, reply_markup=user_markups.after_registration_kb, parse_mode='HTML')
    await state.clear()
