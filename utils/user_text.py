from base.visual.texts import user as user_texts

from aiogram.types import FSInputFile, InlineKeyboardMarkup

from . import split

import vars


def user_questionnaire_text(user_dict: dict, user_data: dict):
    role = user_dict['role']
    if role == 'tutor':
        tags = '#' + '\n#'.join(split.split_subject(user_data['subject']) + ['репетитор'])
        kwargs = {
            'name': user_data['name'],
            'age': user_data['age'],
            'subject': user_data['subject'],
            'experience': user_data['experience'],
            'info': user_data['info'],
            'contacts': user_data['contacts'],
            'price': user_data['price'],
            'tags': tags
        }
        return user_texts.questionnaire_text.format(**kwargs)
    tags = '#' + '\n#'.join(split.split_subject(user_data['subject']) + ['ученик'])
    kwargs = {
        'name': user_data['name'],
        'age': user_data['age'],
        'subject': user_data['subject'],
        'place': user_data['place'],
        'target': user_data['target'],
        'contacts': user_data['contacts'],
        'price': user_data['price'],
        'tags': tags
    }
    return user_texts.tutee_profile_text.format(**kwargs)


def resolve_user_data(user_id: int):
    user = vars.database.get_user(user_id)
    if not user:
        raise ValueError('User not found')
    role = user['role']
    if role == 'tutor':
        user_data = vars.database.get_tutor_data(user_id)
    else:
        user_data = vars.database.get_tutee_data(user_id)
    return user_questionnaire_text(user, user_data), user_data.get('photo_path', None)


async def get_user_screen(user_id: int, chat_id: int, kb: InlineKeyboardMarkup = None):
    text, photo = resolve_user_data(user_id)
    if photo:
        await vars.bot.send_photo(chat_id, FSInputFile(photo), caption=text, reply_markup=kb)
    else:
        await vars.bot.send_message(chat_id, text, reply_markup=kb)
