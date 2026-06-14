from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# --- Кнопки ---
profile_btn = InlineKeyboardButton(text='📋 Моя анкета', callback_data='profile')
put_request_btn = InlineKeyboardButton(text='📤 Подать заявку в канал', callback_data='putRequest')
paid_link_btn_info = InlineKeyboardButton(text='🔗 Опубликовать со ссылкой — 300 ₽', callback_data='paidLinkInfo')
buy_posts_btn = InlineKeyboardButton(text='💰 Купить посты', callback_data='buyPosts')
premium_btn = InlineKeyboardButton(text='💎 Продвижение', callback_data='premiumMenu')
referral_btn = InlineKeyboardButton(text='🔗 Пригласить репетитора', callback_data='myRef')

change_btn = InlineKeyboardButton(text='✏️ Редактировать', callback_data='change')
main_menu_btn = InlineKeyboardButton(text='🏠 Главное меню', callback_data='mainMenu')
cancel_btn = InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')
skip_btn = InlineKeyboardButton(text='Пропустить', callback_data='skip')

tutor_btn = InlineKeyboardButton(text='👨‍🏫 Я репетитор', callback_data='tutor')
student_btn = InlineKeyboardButton(text='🎓 Я ученик', callback_data='student')

want_to_put_request_btn = InlineKeyboardButton(text='📤 Отправить заявку', callback_data='putRequest')
confirm_request_btn = InlineKeyboardButton(text='✅ Подтвердить и отправить', callback_data='confirmRequest')
paid_link_confirm_btn = InlineKeyboardButton(text='✅ Я оплатил — отправить скриншот', callback_data='paidLink')
cancel_payment_btn = InlineKeyboardButton(text='🗑 Убрать ссылку и подать бесплатно', callback_data='cancel')

change_name_btn = InlineKeyboardButton(text='Имя', callback_data='change/name')
change_age_btn = InlineKeyboardButton(text='Возраст', callback_data='change/age')
change_photo_btn = InlineKeyboardButton(text='Фото', callback_data='change/photo_file_id')
change_subject_btn = InlineKeyboardButton(text='Предмет', callback_data='change/subject')
change_experience_btn = InlineKeyboardButton(text='Опыт', callback_data='change/experience')
change_info_btn = InlineKeyboardButton(text='О себе', callback_data='change/info')
change_contacts_btn = InlineKeyboardButton(text='Контакты', callback_data='change/contacts')
change_price_btn = InlineKeyboardButton(text='Цена', callback_data='change/price')
change_place_btn = InlineKeyboardButton(text='Место занятий', callback_data='change/place')
change_target_btn = InlineKeyboardButton(text='Цель обучения', callback_data='change/target')

# --- Клавиатуры ---

main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [profile_btn],
    [put_request_btn],
    [paid_link_btn_info],
    [premium_btn],
    [referral_btn],
    [buy_posts_btn],
])

main_with_admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    [profile_btn],
    [put_request_btn],
    [paid_link_btn_info],
    [premium_btn],
    [referral_btn],
    [buy_posts_btn],
    [InlineKeyboardButton(text='🔧 Админ панель', callback_data='adminPanel')],
])

after_registration_kb = InlineKeyboardMarkup(inline_keyboard=[
    [put_request_btn],
    [profile_btn],
])

profile_kb = InlineKeyboardMarkup(inline_keyboard=[
    [put_request_btn],
    [change_btn],
    [main_menu_btn],
])

change_kb = InlineKeyboardMarkup(inline_keyboard=[
    [change_btn],
    [main_menu_btn],
])

paid_link_kb = InlineKeyboardMarkup(inline_keyboard=[
    [paid_link_confirm_btn],
    [cancel_payment_btn],
])

put_request_kb = InlineKeyboardMarkup(inline_keyboard=[
    [want_to_put_request_btn],
])

confirm_request_kb = InlineKeyboardMarkup(inline_keyboard=[
    [confirm_request_btn],
    [cancel_btn],
])

cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [cancel_btn],
])

skip_kb = InlineKeyboardMarkup(inline_keyboard=[
    [skip_btn],
])

skip_cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [skip_btn],
    [cancel_btn],
])

role_kb = InlineKeyboardMarkup(inline_keyboard=[
    [tutor_btn],
    [student_btn],
])


premium_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔄 Учащённые выходы — 200 ₽/мес', callback_data='buyFrequent')],
    [InlineKeyboardButton(text='📌 Закрепление на 7 дней — 300 ₽', callback_data='buyPin')],
    [InlineKeyboardButton(text='⚡ Комбо: выходы + закреп — 400 ₽', callback_data='buyCombo')],
    [InlineKeyboardButton(text='🏠 Главное меню', callback_data='mainMenu')],
])

premium_pay_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Я оплатил — прислать скриншот', callback_data='sendPremiumScreenshot')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='premiumMenu')],
])


def make_change_kb(is_tutor: bool):
    if is_tutor:
        return InlineKeyboardMarkup(inline_keyboard=[
            [change_name_btn, change_age_btn],
            [change_photo_btn, change_subject_btn],
            [change_experience_btn],
            [change_info_btn],
            [change_contacts_btn, change_price_btn],
            [cancel_btn],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [change_name_btn, change_age_btn],
            [change_subject_btn],
            [change_place_btn],
            [change_target_btn],
            [change_contacts_btn, change_price_btn],
            [cancel_btn],
        ])
