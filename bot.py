import asyncio
import os
from aiogram import Bot, Dispatcher, types
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_KEY)

async def ask_gpt(text):
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

@dp.message()
async def on_message(message: types.Message):
    if not message.text:
        return
    reply = await ask_gpt(message.text)
    await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
