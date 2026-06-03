from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


profile_btn = InlineKeyboardButton(text='Профиль', callback_data='profile')
buy_posts_btn = InlineKeyboardButton(text='Купить посты', callback_data='buyPosts')

change_btn = InlineKeyboardButton(text='Редактировать', callback_data='change')

tutor_btn = InlineKeyboardButton(text='Репетитор', callback_data='tutor')
student_btn = InlineKeyboardButton(text='Ученик', callback_data='student')

change_name_btn = InlineKeyboardButton(text='Имя', callback_data='change/name')
change_age_btn = InlineKeyboardButton(text='Возраст', callback_data='change/age')
change_photo_btn = InlineKeyboardButton(text='Фото', callback_data='change/photo_path')
change_subject_btn = InlineKeyboardButton(text='Предмет', callback_data='change/subject')
change_experience_btn = InlineKeyboardButton(text='Опыт', callback_data='change/experience')
change_info_btn = InlineKeyboardButton(text='Информация о себе', callback_data='change/info')
change_contacts_btn = InlineKeyboardButton(text='Контакты', callback_data='change/contacts')
change_price_btn = InlineKeyboardButton(text='Цена', callback_data='change/price')

change_place_btn = InlineKeyboardButton(text='Место проведения', callback_data='change/place')
change_target_btn = InlineKeyboardButton(text='Цель обучения', callback_data='change/target')

cancel_btn = InlineKeyboardButton(text='Отмена', callback_data='cancel')
main_menu_btn = InlineKeyboardButton(text='Главное меню', callback_data='mainMenu')
skip_btn = InlineKeyboardButton(text='Пропустить', callback_data='skip')

want_to_put_request_btn = InlineKeyboardButton(text='Отправить заявку', callback_data='putRequest')
paid_link_btn = InlineKeyboardButton(text='Я оплатил — отправить скриншот', callback_data='paidLink')
cancel_payment_btn = InlineKeyboardButton(text='Убрать ссылку из анкеты и подать бесплатно', callback_data='cancel')

paid_link_kb = InlineKeyboardMarkup(inline_keyboard=[
    [paid_link_btn],
    [cancel_payment_btn]
])

put_request_kb = InlineKeyboardMarkup(inline_keyboard=[
    [want_to_put_request_btn]
])

main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [profile_btn],
    [want_to_put_request_btn],
    [buy_posts_btn]
])

cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [cancel_btn]
])

profile_kb = InlineKeyboardMarkup(inline_keyboard=[
    [want_to_put_request_btn],
    [change_btn],
    [main_menu_btn]
])

change_kb = InlineKeyboardMarkup(inline_keyboard=[
    [change_btn],
    [main_menu_btn]
])

skip_kb = InlineKeyboardMarkup(inline_keyboard=[
    [skip_btn]
])

change_choose_kb = InlineKeyboardMarkup(inline_keyboard=[
    [change_name_btn, change_age_btn],
    [change_photo_btn, change_subject_btn],
    [change_experience_btn], 
    [change_info_btn],
    [change_contacts_btn, change_price_btn],
    [cancel_btn]
])

role_kb = InlineKeyboardMarkup(inline_keyboard=[
    [tutor_btn],
    [student_btn]
])


def make_change_kb(is_tutor: bool):
    if is_tutor:
        return InlineKeyboardMarkup(inline_keyboard=[
            [change_name_btn, change_age_btn],
            [change_photo_btn, change_subject_btn],
            [change_experience_btn], 
            [change_info_btn],
            [change_contacts_btn, change_price_btn],
            [cancel_btn]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [change_name_btn, change_age_btn],
            [change_subject_btn],
            [change_place_btn],
            [change_target_btn],
            [change_contacts_btn, change_price_btn],
            [cancel_btn]
        ])
