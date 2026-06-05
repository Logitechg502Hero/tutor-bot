from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


requests_btn = InlineKeyboardButton(text='Заявки', callback_data='requests')
find_user_btn = InlineKeyboardButton(text='Найти пользователя', callback_data='findUser')
user_mode_btn = InlineKeyboardButton(text='👤 Режим пользователя', callback_data='userMode')

main_menu_btn = InlineKeyboardButton(text='Главное меню', callback_data='main')
back_to_admin_btn = InlineKeyboardButton(text='🔧 Админ панель', callback_data='adminPanel')


main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [main_menu_btn]
    ])

main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [requests_btn],
    [find_user_btn],
    [user_mode_btn]
    ])


def make_user_kb(user_id: int):
    user_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить пост', callback_data=f'addPost_{user_id}')],
        [main_menu_btn]
    ])
    return user_kb


def make_back_kb(callback_data: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data=callback_data)]
    ])
