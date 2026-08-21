from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    get_user, create_product, update_product, delete_product, get_all_products, get_product,
    get_all_orders, get_orders_by_status, update_order_status, get_low_stock_products,
    get_pending_student_verifications, approve_student, reject_student,
    get_statistics, add_notification
)
from keyboards import admin_menu_keyboard, product_action_keyboard, order_status_keyboard
from states import AddProductForm, EditProductForm
from utils import generate_referral_code

router = Router()

# ---------- ВСПОМОГАТЕЛЬНАЯ ПРОВЕРКА АДМИНА ----------
async def is_admin(user_id: int) -> bool:
    user = get_user(user_id).data
    return user and user[0].get('role') == 'admin'

# ---------- ГЛАВНОЕ АДМИН-МЕНЮ ----------
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ Нет прав.")
        return
    await message.answer("👋 Админ-панель", reply_markup=admin_menu_keyboard())

# ---------- УПРАВЛЕНИЕ ТОВАРАМИ (ДОБАВЛЕНИЕ) ----------
@router.message(F.text == "📦 Управление товарами")
async def admin_products(message: Message):
    if not await is_admin(message.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📋 Список товаров", callback_data="admin_list_products")],
        [InlineKeyboardButton(text="🔍 Найти товар по ID", callback_data="admin_find_product")],
        [InlineKeyboardButton(text="📦 Товары с остатком ≤20", callback_data="admin_low_stock")]
    ])
    await message.answer("Выберите действие:", reply_markup=kb)

# Обработчики кнопок добавления товара
@router.callback_query(F.data == "admin_add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    await state.set_state(AddProductForm.name)
    await callback.message.answer("Введите название товара:")

@router.message(StateFilter(AddProductForm.name))
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProductForm.description)
    await message.answer("Введите описание товара:")

@router.message(StateFilter(AddProductForm.description))
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProductForm.price)
    await message.answer("Введите цену в копейках (например, 1000 = 10 руб):")

@router.message(StateFilter(AddProductForm.price))
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        await state.update_data(price=price)
        await state.set_state(AddProductForm.stock)
        await message.answer("Введите количество на складе:")
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(StateFilter(AddProductForm.stock))
async def add_product_stock(message: Message, state: FSMContext):
    try:
        stock = int(message.text)
        await state.update_data(stock=stock)
        await state.set_state(AddProductForm.category)
        await message.answer("Введите категорию (например, Одежда, Электроника):")
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(StateFilter(AddProductForm.category))
async def add_product_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddProductForm.subcategory)
    await message.answer("Введите подкатегорию (можно пропустить, отправьте 'пропустить'):")

@router.message(StateFilter(AddProductForm.subcategory))
async def add_product_subcategory(message: Message, state: FSMContext):
    sub = message.text if message.text.lower() != "пропустить" else None
    await state.update_data(subcategory=sub)
    await state.set_state(AddProductForm.gender)
    await message.answer("Укажите пол (муж, жен, унисекс) или пропустите:")

@router.message(StateFilter(AddProductForm.gender))
async def add_product_gender(message: Message, state: FSMContext):
    gender = message.text if message.text.lower() != "пропустить" else None
    await state.update_data(gender=gender)
    await state.set_state(AddProductForm.size)
    await message.answer("Введите размер (или пропустите):")

@router.message(StateFilter(AddProductForm.size))
async def add_product_size(message: Message, state: FSMContext):
    size = message.text if message.text.lower() != "пропустить" else None
    await state.update_data(size=size)
    await state.set_state(AddProductForm.color)
    await message.answer("Введите цвет (или пропустите):")

@router.message(StateFilter(AddProductForm.color))
async def add_product_color(message: Message, state: FSMContext):
    color = message.text if message.text.lower() != "пропустить" else None
    await state.update_data(color=color)
    await state.set_state(AddProductForm.image)
    await message.answer("Отправьте фото товара (или нажмите 'пропустить'):")

@router.message(StateFilter(AddProductForm.image), F.photo | F.text)
async def add_product_image(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        # Здесь надо сохранить фото в Supabase Storage и получить URL
        # Пока используем file_id (Telegram) – потом можно заменить на постоянную ссылку
        await state.update_data(image_url=file_id)  # временно
    else:
        await state.update_data(image_url=None)
    
    data = await state.get_data()
    # Создаём товар
    try:
        result = create_product({
            "name": data['name'],
            "description": data['description'],
            "price": data['price'],
            "stock": data['stock'],
            "category": data.get('category'),
            "subcategory": data.get('subcategory'),
            "gender": data.get('gender'),
            "size": data.get('size'),
            "color": data.get('color'),
            "image_url": data.get('image_url'),
            "is_active": True
        })
        if result.data:
            await message.answer(f"✅ Товар добавлен! ID: {result.data[0]['id']}")
        else:
            await message.answer("❌ Ошибка добавления товара.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()

# ---------- РЕДАКТИРОВАНИЕ ТОВАРА (по ID) ----------
@router.callback_query(F.data == "admin_list_products")
async def list_products(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    products = get_all_products(limit=20).data
    if not products:
        await callback.answer("Нет товаров", show_alert=True)
        return
    text = "📋 Последние товары:\n"
    for p in products[:10]:
        text += f"ID: {p['id']} | {p['name']} | {p['price']} коп | Остаток: {p['stock']}\n"
    await callback.message.answer(text)

# ---------- СТАТИСТИКА ----------
@router.message(F.text == "📊 Статистика")
async def admin_statistics(message: Message):
    if not await is_admin(message.from_user.id):
        return
    # Запрашиваем период (можно упростить – последние 30 дней)
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    stats = get_statistics(start_date.isoformat(), end_date.isoformat())
    text = (
        f"📊 **Статистика за 30 дней**\n"
        f"💰 Доход: {stats['total_revenue']} коп\n"
        f"📉 Скидки: {stats['total_discount']} коп\n"
        f"📦 Заказов: {stats['total_orders']}\n"
        f"👤 Новых пользователей: {stats['new_users']}\n"
        f"📦 Активных товаров: {stats['active_products']}\n"
        f"🏆 Топ товаров:\n"
    )
    for p in stats['top_products']:
        text += f"  - {p['name']} (ID {p['id']}) – {p['sales']} продаж\n"
    await message.answer(text)

# ---------- ЗАЯВКИ СТУДЕНТОВ ----------
@router.message(F.text == "🎓 Заявки студентов")
async def pending_students(message: Message):
    if not await is_admin(message.from_user.id):
        return
    verifications = get_pending_student_verifications().data
    if not verifications:
        await message.answer("Нет новых заявок.")
        return
    for v in verifications:
        user = v['users']
        text = f"Заявка от {user['name']} (ID: {user['telegram_id']})\nФото: {v['diary_photo_url']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Подтвердить", callback_data=f"verify_{v['user_id']}_yes")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"verify_{v['user_id']}_no")]
        ])
        await message.answer(text, reply_markup=kb)

# Обработчик подтверждения (уже есть в callback.py – можно перенести сюда или оставить там)
# Но дублируем для надёжности
@router.callback_query(F.data.startswith("verify_"))
async def verify_student(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    parts = callback.data.split("_")
    user_id = int(parts[1])
    action = parts[2]
    if action == "yes":
        approve_student(user_id)
        await callback.answer("Студент подтверждён")
        await callback.message.edit_text("✅ Заявка одобрена")
        # Отправляем уведомление пользователю
        add_notification(user_id, "Ваш студенческий статус подтверждён! Теперь вы можете получать скидки на товары с остатком ≤20.")
    else:
        reject_student(user_id)
        await callback.answer("Отклонено")
        await callback.message.edit_text("❌ Заявка отклонена")
        add_notification(user_id, "К сожалению, ваша заявка на студенческий статус отклонена. Попробуйте загрузить другую фотографию дневника.")

# ---------- ЗАКАЗЫ ----------
@router.message(F.text == "📋 Заказы")
async def admin_orders(message: Message):
    if not await is_admin(message.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Все заказы", callback_data="orders_all")],
        [InlineKeyboardButton("Новые (new)", callback_data="orders_new")],
        [InlineKeyboardButton("Оплаченные (paid)", callback_data="orders_paid")],
        [InlineKeyboardButton("Отправленные (shipped)", callback_data="orders_shipped")],
        [InlineKeyboardButton("Завершённые (completed)", callback_data="orders_completed")],
        [InlineKeyboardButton("Отменённые (cancelled)", callback_data="orders_cancelled")]
    ])
    await message.answer("Выберите статус заказов:", reply_markup=kb)

@router.callback_query(F.data.startswith("orders_"))
async def list_orders(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    status = callback.data.split("_")[1]
    if status == "all":
        orders = get_all_orders(limit=20).data
    else:
        orders = get_orders_by_status(status).data
    if not orders:
        await callback.answer("Нет заказов", show_alert=True)
        return
    text = "📋 Заказы:\n"
    for o in orders[:10]:
        text += f"ID: {o['id']} | Пользователь: {o['user_id']} | Сумма: {o['final_amount']} коп | Статус: {o['status']}\n"
    await callback.message.answer(text)
    await callback.answer()

# ---------- УПРАВЛЕНИЕ СТАТУСОМ ЗАКАЗА (можно добавить кнопки) ----------
# Здесь можно добавить функцию изменения статуса по ID – но пока пропустим, реализуем позже.
