from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_user
from keyboards import admin_menu_keyboard

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    user = get_user(message.from_user.id).data
    if not user or user[0].get('role') != 'admin':
        await message.answer("⛔ У вас нет прав администратора.")
        return
    await message.answer("👋 Добро пожаловать в админ-панель!", reply_markup=admin_menu_keyboard())
