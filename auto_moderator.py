import re


MIN_AGE = 18
MAX_AGE = 70
MIN_PRICE = 100
MIN_INFO_LENGTH = 50

# Паттерн для внешних ссылок — vk, instagram, сайты, t.me/группы
_EXTERNAL_LINK_RE = re.compile(
    r'(https?://|www\.|vk\.com|vk\.cc|instagram\.com|t\.me/[a-zA-Z])',
    re.IGNORECASE
)

PAID_LINK_MESSAGE = (
    'Анкета содержит ссылку на внешний ресурс. '
    'Размещение ссылок — платная функция. '
    'Напишите администратору: @{admin}'
)


def _has_external_link(*fields: str) -> bool:
    for field in fields:
        if field and _EXTERNAL_LINK_RE.search(field):
            return True
    return False


def _has_contact(contacts: str) -> bool:
    if not contacts:
        return False
    has_username = '@' in contacts
    has_phone = bool(re.search(r'[\d\-\+\(\)]{7,}', contacts))
    return has_username or has_phone


def check_tutor(data: dict, admin: str) -> tuple[bool, str, bool]:
    if _has_external_link(data.get('info', ''), data.get('contacts', '')):
        return False, PAID_LINK_MESSAGE.format(admin=admin), True
    if not data.get('name'):
        return False, 'Имя не заполнено', False
    if not data.get('age'):
        return False, 'Возраст не указан', False
    if not (MIN_AGE <= int(data['age']) <= MAX_AGE):
        return False, f'Возраст должен быть от {MIN_AGE} до {MAX_AGE} лет', False
    if not data.get('subject'):
        return False, 'Предмет не указан', False
    if not data.get('experience'):
        return False, 'Опыт не указан', False
    if not data.get('info') or len(data['info']) < MIN_INFO_LENGTH:
        return False, f'Описание слишком короткое (минимум {MIN_INFO_LENGTH} символов)', False
    if not data.get('contacts'):
        return False, 'Контакты не заполнены', False
    if not _has_contact(data['contacts']):
        return False, 'Контакты должны содержать @ или номер телефона', False
    if not data.get('price'):
        return False, 'Цена не указана', False
    if float(data['price']) < MIN_PRICE:
        return False, f'Цена должна быть не менее {MIN_PRICE} руб/час', False
    return True, '', False


def check_tutee(data: dict, admin: str) -> tuple[bool, str, bool]:
    if _has_external_link(data.get('target', ''), data.get('contacts', '')):
        return False, PAID_LINK_MESSAGE.format(admin=admin), True
    if not data.get('name'):
        return False, 'Имя не заполнено', False
    if not data.get('age'):
        return False, 'Возраст не указан', False
    if not (MIN_AGE <= int(data['age']) <= MAX_AGE):
        return False, f'Возраст должен быть от {MIN_AGE} до {MAX_AGE} лет', False
    if not data.get('subject'):
        return False, 'Предмет не указан', False
    if not data.get('place'):
        return False, 'Формат обучения не указан', False
    if not data.get('target'):
        return False, 'Цель обучения не заполнена', False
    if not data.get('contacts'):
        return False, 'Контакты не заполнены', False
    if not _has_contact(data['contacts']):
        return False, 'Контакты должны содержать @ или номер телефона', False
    if not data.get('price'):
        return False, 'Цена не указана', False
    if float(data['price']) < MIN_PRICE:
        return False, f'Цена должна быть не менее {MIN_PRICE} руб/час', False
    return True, '', False


def moderate(user: dict, user_data: dict, admin: str) -> tuple[bool, str, bool]:
    if user['role'] == 'tutor':
        return check_tutor(user_data, admin)
    return check_tutee(user_data, admin)
