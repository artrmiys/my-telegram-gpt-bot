import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import OpenAI

# Убираем прокси из окружения (GitHub Actions их ставит)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()

# Новый правильный клиент
client = OpenAI(api_key=OPENAI_KEY)

async def ask_gpt(text):
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": text}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка GPT: {e}"

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("✅ Привет! Я работаю, пиши что угодно.")

@dp.message()
async def handle_all(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
