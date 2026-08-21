import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def check_admin_exists():
    """Проверяет, есть ли в таблице users хотя бы один admin."""
    response = supabase.table("users").select("id").eq("role", "admin").limit(1).execute()
    if not response.data:
        logging.warning("В базе нет администраторов! Добавьте хотя бы одного через SQL.")

# --- Функции для пользователей ---
def get_user(telegram_id: int):
    return supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()

def create_user(telegram_id: int, name: str, phone: str = None):
    data = {
        "telegram_id": telegram_id,
        "name": name,
        "phone": phone,
        "role": "user"
    }
    return supabase.table("users").insert(data).execute()

# --- Функции для товаров ---
def get_all_products(limit: int = 100):
    return supabase.table("products").select("*").eq("is_active", True).limit(limit).execute()

def get_product(product_id: int):
    return supabase.table("products").select("*").eq("id", product_id).execute()

def create_product(name, description, price, stock, category, subcategory, gender, size, color, image_url):
    data = {
        "name": name,
        "description": description,
        "price": price,
        "stock": stock,
        "category": category,
        "subcategory": subcategory,
        "gender": gender,
        "size": size,
        "color": color,
        "image_url": image_url,
        "is_active": True
    }
    return supabase.table("products").insert(data).execute()

def update_product(product_id: int, **kwargs):
    return supabase.table("products").update(kwargs).eq("id", product_id).execute()

def delete_product(product_id: int):
    return supabase.table("products").update({"is_active": False}).eq("id", product_id).execute()
