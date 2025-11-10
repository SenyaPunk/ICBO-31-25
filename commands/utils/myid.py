from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("myid"))
async def cmd_myid(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    response = f"📋 <b>Ваша информация:</b>\n\n"
    response += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
    
    if username:
        response += f"👤 <b>Username:</b> @{username}\n"
    
    response += f"📝 <b>Имя:</b> {first_name}"
    
    await message.answer(response)
