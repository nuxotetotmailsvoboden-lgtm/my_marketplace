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
from database import get_user, update_user, generate_referral_code, add_notification
from keyboards import main_menu_keyboard
from states import StudentVerifyForm

@router.message(F.text == "👤 Мой профиль")
async def profile(message: Message):
    user_data = get_user(message.from_user.id).data
    if not user_data:
        await message.answer("Вы не зарегистрированы. Напишите /start")
        return
    u = user_data[0]
    text = (
        f"👤 **Профиль**\n"
        f"Имя: {u['name']}\n"
        f"Телефон: {u['phone'] or 'не указан'}\n"
        f"Заказов: {u['total_orders']}\n"
        f"Кэшбэк: {u['cashback_balance']} коп\n"
        f"Статус студента: {u['student_status']}\n"
        f"Реферальный код: {u['referral_code'] or 'нет'}"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())

@router.message(F.text == "🔗 Реферальная ссылка")
async def referral_link(message: Message):
    user = get_user(message.from_user.id).data
    if not user:
        await message.answer("Сначала зарегистрируйтесь /start")
        return
    u = user[0]
    if not u.get('referral_code'):
        # Генерируем код и сохраняем
        code = generate_referral_code()
        update_user(message.from_user.id, referral_code=code)
        u['referral_code'] = code
    link = f"https://t.me/ваш_бот?start=ref_{u['referral_code']}"
    await message.answer(f"Ваша реферальная ссылка:\n{link}\n\nПриглашайте друзей и получайте 10% скидку на первый заказ!")

@router.message(F.text == "🎓 Студентам")
async def student_info(message: Message):
    await message.answer(
        "🎓 **Студенческая скидка**\n"
        "Если вы студент или школьник, загрузите фото дневника/ведомости с оценками.\n"
        "Мы проверим и если у вас есть 4 и 5 (или успеваемость >80%), вы получите скидку 10% на товары с остатком ≤20!\n"
        "Скидка действует раз в неделю.\n\n"
        "Для загрузки фото используйте команду /verify_student"
    )

@router.message(Command("verify_student"))
async def start_verify_student(message: Message, state: FSMContext):
    user = get_user(message.from_user.id).data
    if not user:
        await message.answer("Сначала зарегистрируйтесь /start")
        return
    if user[0].get('student_status') == 'approved':
        await message.answer("Вы уже подтверждены как студент.")
        return
    await state.set_state(StudentVerifyForm.photo)
    await message.answer("Отправьте фото дневника с оценками (чёткое фото).")

@router.message(StateFilter(StudentVerifyForm.photo), F.photo)
async def verify_student_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    # Сохраняем фото в Supabase Storage (позже), пока просто сохраняем file_id
    photo_url = file_id  # временно
    from database import create_student_verification
    create_student_verification(message.from_user.id, photo_url)
    await state.clear()
    await message.answer("✅ Фото отправлено на проверку. Мы уведомим вас о результате.")
    # Уведомление админам – можно отправить в группу или в чат админа (пока пропустим)
