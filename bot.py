import asyncio
import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()

async def ask_gpt(text):
    try:
        resp = openai.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": text}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка GPT: {e}"

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("✅ Бот запущен! Просто напиши текст.")

@dp.message()
async def on_message(message: types.Message):
    print("[LOG]", message.text)
    reply = await ask_gpt(message.text)
    await message.answer(reply)

async def main():
    print("🚀 Бот запущен и слушает...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
