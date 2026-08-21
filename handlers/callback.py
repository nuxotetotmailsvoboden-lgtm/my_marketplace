from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import supabase

router = Router()

@router.callback_query(F.data.startswith("verify_student_"))
async def verify_student_callback(callback: CallbackQuery):
    data = callback.data.split("_")
    action = data[2]
    user_id = int(data[3])
    
    # Проверяем, что вызывающий – админ
    admin = supabase.table("users").select("role").eq("telegram_id", callback.from_user.id).execute()
    if not admin.data or admin.data[0]['role'] != 'admin':
        await callback.answer("⛔ Только для админов", show_alert=True)
        return
    
    if action == "yes":
        # Обновляем статус студента
        supabase.table("users").update({"student_status": "approved"}).eq("telegram_id", user_id).execute()
        await callback.answer("✅ Студент подтверждён")
        await callback.message.edit_text("✅ Заявка одобрена")
    else:
        supabase.table("users").update({"student_status": "rejected"}).eq("telegram_id", user_id).execute()
        await callback.answer("❌ Отклонено")
        await callback.message.edit_text("❌ Заявка отклонена")
