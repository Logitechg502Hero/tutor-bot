from aiogram.fsm.state import StatesGroup, State


class RequestsStates(StatesGroup):
    main = State()
    reject_reason = State()
