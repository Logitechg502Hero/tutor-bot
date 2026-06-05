# Tutor Bot — статус проекта

**GitHub:** https://github.com/Logitechg502Hero/tutor-bot  
**Деплой:** Railway (auto-deploy от main)  
**Канал:** @repetitor_msc  
**Последний коммит:** feat: UX, broadcast, edit_text, прогресс анкеты, статистика в админке

---

## Что работает

### Пользователи
- Регистрация репетитора (8 шагов с прогрессом) и ученика (6 шагов)
- Кнопка «Отмена» на каждом шаге + отмена текстом («отмена», /cancel)
- Просмотр и редактирование анкеты
- Подача заявки с превью анкеты перед отправкой
- Платное размещение ссылки (300 руб., скриншот → admin)
- Рейтинг и отзывы для репетиторов (1–5 звёзд + комментарий)
- Персональное главное меню «Привет, {name}!»

### Публикация
- Посты уходят в канал в 12:00 и 19:00 по очереди
- Через 7 дней после публикации — напоминание переразместить
- Редактирование анкеты автоматически ставит заявку на повторную публикацию
- Платное размещение в конкретное время (admin назначает дату)
- Еженедельная статистика репетиторам (воскресенье 18:00): просмотры + рейтинг

### Админка (/start для admin)
- Главный экран: статистика (репетиторы, ученики, на модерации, опубликовано за 7 дней)
- Заявки на модерацию: листалка, одобрить/отказать с причиной, счётчик «X из Y»
- При одобрении — юзер получает уведомление
- Поиск пользователя по ID, просмотр анкеты, назначение даты поста
- Рассылка: всем / только репетиторам / только ученикам, с превью
- Переключение admin ↔ пользователь через кнопку в меню
- Войти в админку: /admin pass

### Веб-дашборд
- URL: https://твой-домен.railway.app (порт 8080)
- Логин: alan / pass (из .env: DASHBOARD_LOGIN / DASHBOARD_PASSWORD)
- Показывает: кол-во юзеров, на модерации, опубликовано, рейтинг, запланировано
- Таблица последних 20 пользователей
- Авто-обновление каждые 60 секунд

---

## Архитектура

```
main.py              — точка входа, asyncio.run()
vars.py              — глобальные объекты (bot, database, admin_ids, post_scheduler)
database.py          — aiosqlite, все методы async
auto_moderator.py    — валидация анкет
post_scheduler.py    — APScheduler: публикации, напоминания, weekly stats
filters.py           — AdminFilter (кеш в памяти, не DB на каждый запрос)
dashboard.py         — Flask дашборд, Basic Auth
base/handlers/user/  — регистрация, профиль, редактирование, отзывы
base/handlers/admin/ — модерация, поиск, рассылка
base/visual/         — тексты и клавиатуры
utils/user_text.py   — форматирование анкеты + рейтинг
```

### Таблицы БД
| Таблица | Ключевые поля |
|---|---|
| users | user_id, role, created_at |
| tutors | user_id, name, age, **photo_file_id**, subject, experience, info, contacts, price |
| tutees | user_id, name, age, subject, place, target, contacts, price |
| requests | user_id, status (pending/approved/finished/rejected), created_at |
| scheduled_posts | post_id, user_id, post_date, status |
| reviews | tutor_id, reviewer_id, rating(1-5), comment, UNIQUE(tutor_id, reviewer_id) |
| profile_views | tutor_id, viewed_at |
| admins | admin_id |

---

## .env

```
bot_token=...
bot_password=pass
chat_id=-1001338967944
admin_username=Ts_alan
DASHBOARD_LOGIN=alan
DASHBOARD_PASSWORD=pass
DASHBOARD_PORT=8080
```

---

## Важные технические решения

- **photo_file_id** вместо локальных файлов — Railway не сохраняет файлы между деплоями
- **admin_ids** — set в памяти, обновляется при /admin, не ходит в БД на каждый апдейт
- **asyncio.run()** — post_scheduler создаётся внутри main() уже после старта event loop
- **edit_text** вместо answer в callbacks — нет спама новых сообщений
- **aiosqlite** вместо sqlite3 — нет блокировок event loop под нагрузкой
- Возраст: репетитор от 18, ученик от 6

---

## Что можно сделать дальше (отложено)

- Каталог репетиторов с фильтрами (предмет, цена, формат)
- Личные сообщения ученик → репетитор через бота
- Реферальная система
- Оплата через Telegram Payments / ЮКасса
