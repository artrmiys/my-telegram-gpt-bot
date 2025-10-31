import asyncio
import os
import openai
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

async def ask_gpt(text):
    resp = openai.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": text}]
    )
    return resp.choices[0].message.content

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✅ Я запущен! Напиши мне любое сообщение.")

@router.message()
async def on_message(message: types.Message):
    # реагируем только на личку
    if message.chat.type != "private":
        return
    
    reply = await ask_gpt(message.text)
    await message.answer(reply)

async def main():
    print("✅ Bot started and waiting for your DM...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
