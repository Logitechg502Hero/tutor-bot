from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):

    find_user_id = State()

    add_post_date = State()
