import asyncio
import os
import openai
from aiogram import Bot, Dispatcher, types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()

async def ask_gpt(text):
    resp = openai.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": text}]
    )
    return resp.choices[0].message.content

@dp.message()
async def on_message(message: types.Message):
    # Ловим любые сообщения в ЛИЧКЕ
    if message.chat.type != "private":
        return

    if not message.text:
        await message.answer("Пришли текст 🙃")
        return

    reply = await ask_gpt(message.text)
    await message.answer(reply)

async def main():
    print("✅ Bot started and waiting for messages...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
