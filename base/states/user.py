from aiogram.fsm.state import StatesGroup, State


class UserStates(StatesGroup):
    input_role = State()
    input_name = State()
    input_age = State()
    input_photo = State()
    input_subject = State()
    input_experience = State()
    input_info = State()
    input_contacts = State()
    input_price = State()

    change_value = State()

    tutee_input_name = State()
    tutee_input_age = State()
    tutee_input_subject = State()
    tutee_input_place = State()
    tutee_input_target = State()
    tutee_input_price = State()
    tutee_input_contacts = State()

    confirm_request = State()
    awaiting_payment_screenshot = State()

    review_rating = State()
    review_comment = State()

    awaiting_premium_screenshot = State()
