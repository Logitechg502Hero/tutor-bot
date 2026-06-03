from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from base.states.user import UserStates

from base.visual.texts import user as user_texts
from base.visual.markups import user as user_markups

from utils import validate, split

import constants

import vars


router = Router()


@router.callback_query(F.data == 'tutor')
async def input_role_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(user_texts.input_name_text)
    await state.set_state(UserStates.input_name)
    await callback.answer(show_alert=False)


@router.message(UserStates.input_name, F.text)
async def input_name_handler(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(user_texts.input_age_text)
    await state.set_state(UserStates.input_age)


@router.message(UserStates.input_age, F.text)
async def input_age_handler(message: Message, state: FSMContext):
    if not validate.validate_age(message.text):
        await message.answer(user_texts.invalid_age_text)
        return
    await state.update_data(age=int(message.text))
    await message.answer(user_texts.input_photo_text, reply_markup=user_markups.skip_kb)
    await state.set_state(UserStates.input_photo)


@router.message(UserStates.input_photo, F.photo)
async def input_photo_handler(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer(user_texts.input_subject_text)
    await state.set_state(UserStates.input_subject)


@router.callback_query(UserStates.input_photo, F.data == 'skip')
async def skip_photo_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    await callback.message.answer(user_texts.input_subject_text)
    await state.set_state(UserStates.input_subject)
    await callback.answer(show_alert=False)


@router.message(UserStates.input_subject, F.text)
async def input_subject_handler(message: Message, state: FSMContext):
    subject = ', '.join(split.split_subject(message.text))
    await state.update_data(subject=subject)
    await message.answer(user_texts.input_experience_text)
    await state.set_state(UserStates.input_experience)


@router.message(UserStates.input_experience, F.text)
async def input_experience_handler(message: Message, state: FSMContext):
    if not validate.validate_experience(message.text):
        await message.answer(user_texts.invalid_experience_text)
        return
    await state.update_data(experience=int(message.text))
    await message.answer(user_texts.input_info_text)
    await state.set_state(UserStates.input_info)


@router.message(UserStates.input_info, F.text)
async def input_info_handler(message: Message, state: FSMContext):
    if not validate.validate_info(message.text):
        await message.answer(user_texts.invalid_info_text)
        return
    await state.update_data(info=message.text)
    await message.answer(user_texts.input_contacts_text)
    await state.set_state(UserStates.input_contacts)


@router.message(UserStates.input_contacts, F.text)
async def input_contacts_handler(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await message.answer(user_texts.input_price_text)
    await state.set_state(UserStates.input_price)


@router.message(UserStates.input_price, F.text)
async def input_price_handler(message: Message, state: FSMContext, bot: Bot):
    if not validate.validate_price(message.text):
        await message.answer(user_texts.invalid_price_text)
        return
    
    data = await state.get_data()
    name = data['name']
    age = data['age']
    photo = data['photo']
    subject = data['subject']
    experience = data['experience']
    info = data['info']
    contacts = data['contacts']
    price = float(message.text)

    vars.database.create_user(
        user_id=message.from_user.id,
        role='tutor',
        name=name,
        age=age,
        photo_path=photo,
        subject=subject,
        experience=experience,
        info=info,
        contacts=contacts,
        price=price
    )

    await message.answer(user_texts.questionnaire_filled_text, reply_markup=user_markups.after_registration_kb)
    await state.clear()
