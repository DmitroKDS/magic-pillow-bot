from aiogram.fsm.state import StatesGroup, State

class create_pil_img(StatesGroup):
    is_waiting = State()
    processing = State()

class pil_other_count(StatesGroup):
    is_waiting = State()