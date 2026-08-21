from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from database import create_user, get_user
from keyboards import main_menu_keyboard
from states import RegisterForm

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id).data
    if user:
        # Уже зарегистрирован
        await message.answer(
            f"👋 С возвращением, {user[0]['name']}!",
            reply_markup=main_menu_keyboard()
        )
    else:
        # Начинаем регистрацию
        await state.set_state(RegisterForm.name)
        await message.answer(
            "👋 Добро пожаловать в наш маркетплейс!\n"
            "Давай познакомимся. Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove()
        )

@router.message(RegisterForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RegisterForm.phone)
    # Запрос телефона с кнопкой
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Отлично! Теперь укажи номер телефона.", reply_markup=keyboard)

@router.message(RegisterForm.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    contact = message.contact
    data = await state.get_data()
    name = data['name']
    phone = contact.phone_number

    # Сохраняем в БД
    create_user(message.from_user.id, name, phone)
    await state.clear()

    await message.answer(
        f"🎉 Регистрация завершена, {name}!\n"
        "Теперь ты можешь пользоваться маркетплейсом.",
        reply_markup=main_menu_keyboard()
    )
