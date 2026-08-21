from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- Главное меню пользователя ---
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Каталог")],
            [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="🎓 Студентам")],
            [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="📦 Мои заказы")],
            [KeyboardButton(text="🔗 Реферальная ссылка")]
        ],
        resize_keyboard=True
    )

# --- Админ-меню ---
def admin_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Управление товарами")],
            [KeyboardButton(text="📋 Заказы"), KeyboardButton(text="🎓 Заявки студентов")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )

# --- Inline клавиатура для подтверждения студента ---
def student_verify_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"verify_student_yes_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"verify_student_no_{user_id}")
        ]

# --- Клавиатура для действий с товаром ---
def product_action_keyboard(product_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_product_{product_id}")],
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_product_{product_id}")],
        [InlineKeyboardButton("📦 Изменить остаток", callback_data=f"change_stock_{product_id}")]
    ])

def order_status_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"order_paid_{order_id}")],
        [InlineKeyboardButton("📦 Отправить", callback_data=f"order_shipped_{order_id}")],
        [InlineKeyboardButton("✅ Завершить", callback_data=f"order_completed_{order_id}")],
        [InlineKeyboardButton("❌ Отменить", callback_data=f"order_cancelled_{order_id}")]
    ])
    ])
