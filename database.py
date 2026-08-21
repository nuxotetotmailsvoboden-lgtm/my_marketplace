import os
import logging
from datetime import datetime, timedelta
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Проверка админа ----------
async def check_admin_exists():
    response = supabase.table("users").select("id").eq("role", "admin").limit(1).execute()
    if not response.data:
        logging.warning("⚠️ В базе нет администраторов! Добавьте через SQL.")

# ---------- ПОЛЬЗОВАТЕЛИ ----------
def get_user(telegram_id: int):
    return supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()

def create_user(telegram_id: int, name: str, phone: str = None, referred_by: int = None):
    data = {
        "telegram_id": telegram_id,
        "name": name,
        "phone": phone,
        "role": "user",
        "referred_by": referred_by,
    }
    return supabase.table("users").insert(data).execute()

def update_user(telegram_id: int, **kwargs):
    return supabase.table("users").update(kwargs).eq("telegram_id", telegram_id).execute()

def get_all_users(limit=1000):
    return supabase.table("users").select("*").limit(limit).execute()

# ---------- ТОВАРЫ ----------
def get_all_products(limit=100):
    return supabase.table("products").select("*").eq("is_active", True).limit(limit).execute()

def get_product(product_id: int):
    return supabase.table("products").select("*").eq("id", product_id).execute()

def create_product(data: dict):
    return supabase.table("products").insert(data).execute()

def update_product(product_id: int, data: dict):
    return supabase.table("products").update(data).eq("id", product_id).execute()

def delete_product(product_id: int):
    return supabase.table("products").update({"is_active": False}).eq("id", product_id).execute()

def get_products_by_category(category: str):
    return supabase.table("products").select("*").eq("category", category).eq("is_active", True).execute()

def get_low_stock_products(threshold=20):
    """Товары с остатком <= threshold (для акции)."""
    return supabase.table("products").select("*").lte("stock", threshold).gt("stock", 0).eq("is_active", True).execute()

# ---------- ЗАКАЗЫ ----------
def create_order(order_data: dict):
    return supabase.table("orders").insert(order_data).execute()

def get_order(order_id: int):
    return supabase.table("orders").select("*").eq("id", order_id).execute()

def get_orders_by_user(user_id: int):
    return supabase.table("orders").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

def get_all_orders(limit=100):
    return supabase.table("orders").select("*").order("created_at", desc=True).limit(limit).execute()

def update_order_status(order_id: int, status: str):
    return supabase.table("orders").update({"status": status}).eq("id", order_id).execute()

def get_orders_by_status(status: str):
    return supabase.table("orders").select("*").eq("status", status).order("created_at", desc=True).execute()

# ---------- РЕФЕРАЛЬНАЯ СИСТЕМА ----------
def get_referral_usage(referee_id: int):
    """Проверяем, использовал ли реферер скидку за этого пользователя."""
    return supabase.table("referral_usage").select("*").eq("referee_id", referee_id).execute()

def create_referral_usage(referrer_id: int, referee_id: int, order_id: int, discount: int):
    data = {
        "referrer_id": referrer_id,
        "referee_id": referee_id,
        "order_id": order_id,
        "discount_applied": discount
    }
    return supabase.table("referral_usage").insert(data).execute()

def get_user_first_order_date(user_id: int):
    orders = supabase.table("orders").select("created_at").eq("user_id", user_id).order("created_at").limit(1).execute()
    return orders.data[0]['created_at'] if orders.data else None

# ---------- СТУДЕНЧЕСКАЯ СКИДКА ----------
def create_student_verification(user_id: int, photo_url: str):
    data = {"user_id": user_id, "diary_photo_url": photo_url, "status": "pending"}
    return supabase.table("student_verification").insert(data).execute()

def get_pending_student_verifications():
    return supabase.table("student_verification").select("*, users(name, telegram_id)").eq("status", "pending").execute()

def approve_student(user_id: int, verified_at: datetime = None):
    if not verified_at:
        verified_at = datetime.now()
    # Обновляем статус в users
    update_user(user_id, student_status="approved", student_verified_at=verified_at.isoformat())
    # Обновляем заявку
    return supabase.table("student_verification").update({"status": "approved", "verified_at": verified_at.isoformat()}).eq("user_id", user_id).eq("status", "pending").execute()

def reject_student(user_id: int, comment: str = None):
    update_user(user_id, student_status="rejected")
    return supabase.table("student_verification").update({"status": "rejected", "admin_comment": comment}).eq("user_id", user_id).eq("status", "pending").execute()

def get_student_discount_usage(user_id: int, week_start: str):
    """Проверяем, использовал ли студент скидку на этой неделе."""
    return supabase.table("student_discount_usage").select("*").eq("user_id", user_id).eq("week_start", week_start).execute()

def create_student_discount_usage(user_id: int, order_id: int, week_start: str, discount: int):
    data = {
        "user_id": user_id,
        "order_id": order_id,
        "week_start": week_start,
        "discount_applied": discount
    }
    return supabase.table("student_discount_usage").insert(data).execute()

# ---------- КЭШБЭК ----------
def get_cashback_balance(user_id: int):
    """Возвращает текущий баланс кэшбэка (с учётом истечения)."""
    response = supabase.table("cashback_history").select("amount, type, expires_at").eq("user_id", user_id).execute()
    balance = 0
    for record in response.data:
        if record['type'] == 'earned' and (record['expires_at'] is None or datetime.fromisoformat(record['expires_at']) > datetime.now()):
            balance += record['amount']
        elif record['type'] == 'spent':
            balance -= record['amount']
        # истёкшие не учитываем
    return balance

def add_cashback(user_id: int, order_id: int, amount: int, expires_days: int = 15):
    expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
    data = {
        "user_id": user_id,
        "order_id": order_id,
        "amount": amount,
        "type": "earned",
        "expires_at": expires_at
    }
    return supabase.table("cashback_history").insert(data).execute()

def spend_cashback(user_id: int, order_id: int, amount: int):
    data = {
        "user_id": user_id,
        "order_id": order_id,
        "amount": amount,
        "type": "spent"
    }
    return supabase.table("cashback_history").insert(data).execute()

def get_expired_cashback(user_id: int):
    """Возвращает сумму истёкшего кэшбэка (для уведомлений)."""
    now = datetime.now().isoformat()
    response = supabase.table("cashback_history").select("amount").eq("user_id", user_id).eq("type", "earned").lt("expires_at", now).execute()
    return sum(r['amount'] for r in response.data)

# ---------- СТАТИСТИКА ----------
def get_statistics(start_date: str, end_date: str):
    """
    Возвращает: доход, сумму скидок, количество заказов, количество новых пользователей,
    топ-5 товаров по продажам, количество активных товаров.
    start_date и end_date в формате ISO (YYYY-MM-DD).
    """
    # Заказы за период
    orders = supabase.table("orders").select("*").gte("created_at", start_date).lte("created_at", end_date).execute()
    total_revenue = 0
    total_discount = 0
    total_orders = len(orders.data)
    product_sales = {}
    for order in orders.data:
        total_revenue += order['final_amount']
        total_discount += order['discount_applied']
        # Считаем продажи по товарам
        if order['product_ids']:
            for pid in order['product_ids']:
                product_sales[pid] = product_sales.get(pid, 0) + 1

    # Новые пользователи
    new_users = supabase.table("users").select("id").gte("created_at", start_date).lte("created_at", end_date).execute()
    new_users_count = len(new_users.data)

    # Топ товаров
    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    top_products_data = []
    for pid, sales_count in top_products:
        product = supabase.table("products").select("name").eq("id", pid).execute()
        if product.data:
            top_products_data.append({"id": pid, "name": product.data[0]['name'], "sales": sales_count})

    # Активные товары
    active_products = supabase.table("products").select("id").eq("is_active", True).execute()
    active_count = len(active_products.data)

    return {
        "total_revenue": total_revenue,
        "total_discount": total_discount,
        "total_orders": total_orders,
        "new_users": new_users_count,
        "top_products": top_products_data,
        "active_products": active_count
    }

# ---------- УВЕДОМЛЕНИЯ ----------
def add_notification(user_id: int, message: str):
    data = {"user_id": user_id, "message": message}
    return supabase.table("notifications").insert(data).execute()

def get_unread_notifications(user_id: int):
    return supabase.table("notifications").select("*").eq("user_id", user_id).eq("is_read", False).execute()

def mark_notification_read(notification_id: int):
    return supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
