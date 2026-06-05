from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from base.states.user import UserStates
from base.visual.markups import user as user_markups

import vars


router = Router()

_STARS = {1: '⭐️', 2: '⭐️⭐️', 3: '⭐️⭐️⭐️', 4: '⭐️⭐️⭐️⭐️', 5: '⭐️⭐️⭐️⭐️⭐️'}

_rating_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=s, callback_data=f'rate_{r}') for r, s in _STARS.items()]
])

_skip_comment_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Пропустить', callback_data='skipComment')]
])


@router.callback_query(F.data.startswith('leaveReview_'))
async def leave_review_start(callback: CallbackQuery, state: FSMContext):
    tutor_id = int(callback.data.split('_')[1])
    reviewer_id = callback.from_user.id
    if tutor_id == reviewer_id:
        await callback.answer('Нельзя оставить отзыв самому себе.', show_alert=True)
        return
    if await vars.database.has_reviewed(tutor_id, reviewer_id):
        await callback.answer('Вы уже оставляли отзыв этому репетитору.', show_alert=True)
        return
    await state.update_data(review_tutor_id=tutor_id)
    await state.set_state(UserStates.review_rating)
    await callback.message.answer('Поставьте оценку репетитору:', reply_markup=_rating_kb)
    await callback.answer(show_alert=False)


@router.callback_query(UserStates.review_rating, F.data.startswith('rate_'))
async def leave_review_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split('_')[1])
    await state.update_data(review_rating=rating)
    await state.set_state(UserStates.review_comment)
    await callback.message.answer('Напишите комментарий (или нажмите «Пропустить»):', reply_markup=_skip_comment_kb)
    await callback.answer(show_alert=False)


@router.message(UserStates.review_comment, F.text)
async def leave_review_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    await vars.database.add_review(data['review_tutor_id'], message.from_user.id, data['review_rating'], message.text)
    await state.clear()
    await message.answer('✅ Отзыв сохранён! Спасибо.', reply_markup=user_markups.main_kb)


@router.callback_query(UserStates.review_comment, F.data == 'skipComment')
async def skip_review_comment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await vars.database.add_review(data['review_tutor_id'], callback.from_user.id, data['review_rating'], None)
    await state.clear()
    await callback.message.answer('✅ Отзыв сохранён! Спасибо.', reply_markup=user_markups.main_kb)
    await callback.answer(show_alert=False)


@router.callback_query(F.data.startswith('viewReviews_'))
async def view_reviews(callback: CallbackQuery):
    tutor_id = int(callback.data.split('_')[1])
    reviews = await vars.database.get_tutor_reviews(tutor_id, limit=5)
    if not reviews:
        await callback.answer('У этого репетитора пока нет отзывов.', show_alert=True)
        return
    lines = []
    for r in reviews:
        stars = _STARS.get(r['rating'], '')
        comment = f'\n💬 {r["comment"]}' if r['comment'] else ''
        lines.append(f'{stars}{comment}')
    await callback.message.answer('📝 Последние отзывы:\n\n' + '\n\n'.join(lines))
    await callback.answer(show_alert=False)
