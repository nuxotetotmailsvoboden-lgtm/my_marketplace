import secrets
import string

def generate_referral_code():
    """Генерирует уникальный код из 6 символов."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))

def calculate_referral_discount(total_amount: int) -> int:
    """10% скидка (возвращает сумму скидки в копейках)."""
    return int(total_amount * 0.1)

def calculate_student_discount(total_amount: int) -> int:
    """10% скидка для студентов."""
    return int(total_amount * 0.1)

def calculate_cashback(amount: int, total_orders: int) -> int:
    """Расчёт кэшбэка в зависимости от количества заказов."""
    if total_orders >= 20:
        return int(amount * 0.1)
    elif total_orders >= 10:
        return int(amount * 0.1)
    elif total_orders >= 3:
        return int(amount * 0.05)
    else:
        return 0
