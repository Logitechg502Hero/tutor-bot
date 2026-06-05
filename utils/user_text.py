from base.visual.texts import user as user_texts
from aiogram.types import InlineKeyboardMarkup
from . import split
import vars


def user_questionnaire_text(user_dict: dict, user_data: dict, rating: tuple[float, int] | None = None) -> str:
    role = user_dict['role']
    if role == 'tutor':
        tags = '#' + '\n#'.join(split.split_subject(user_data['subject']) + ['репетитор'])
        if rating and rating[1] > 0:
            rating_str = f'⭐️ Рейтинг: {rating[0]} ({rating[1]} отзывов)'
        else:
            rating_str = 'Отзывов пока нет'
        return user_texts.questionnaire_text.format(
            name=user_data['name'],
            age=user_data['age'],
            subject=user_data['subject'],
            experience=user_data['experience'],
            info=user_data['info'],
            contacts=user_data['contacts'],
            price=user_data['price'],
            rating=rating_str,
            tags=tags
        )
    tags = '#' + '\n#'.join(split.split_subject(user_data['subject']) + ['ученик'])
    return user_texts.tutee_profile_text.format(
        name=user_data['name'],
        age=user_data['age'],
        subject=user_data['subject'],
        place=user_data['place'],
        target=user_data['target'],
        contacts=user_data['contacts'],
        price=user_data['price'],
        tags=tags
    )


async def resolve_user_data(user_id: int) -> tuple[str, str | None]:
    user = await vars.database.get_user(user_id)
    if not user:
        raise ValueError('User not found')
    role = user['role']
    if role == 'tutor':
        user_data = await vars.database.get_tutor_data(user_id)
        rating = await vars.database.get_tutor_rating(user_id)
    else:
        user_data = await vars.database.get_tutee_data(user_id)
        rating = None
    photo_id = user_data.get('photo_file_id') if role == 'tutor' else None
    return user_questionnaire_text(user, user_data, rating), photo_id


async def get_user_screen(user_id: int, chat_id: int, kb: InlineKeyboardMarkup = None):
    text, photo_id = await resolve_user_data(user_id)
    if photo_id:
        await vars.bot.send_photo(chat_id, photo_id, caption=text, reply_markup=kb)
    else:
        await vars.bot.send_message(chat_id, text, reply_markup=kb)
