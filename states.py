from aiogram.fsm.state import State, StatesGroup

class RegisterForm(StatesGroup):
    name = State()
    phone = State()
    referral_code = State()

class AddProductForm(StatesGroup):
    name = State()
    description = State()
    price = State()
    stock = State()
    category = State()
    subcategory = State()
    gender = State()
    size = State()
    color = State()
    image = State()
    
class StudentVerifyForm(StatesGroup):
    photo = State()
