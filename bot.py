import os
import asyncio
import openai
from aiogram import Bot, Dispatcher, types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
openai.api_key = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()

async def ask_gpt(text):
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты остроумный помощник с чёрным юмором. Отвечай дерзко, но умно. Не перебарщивай с матом."},
            {"role": "user", "content": text}
        ]
    )
    return resp.choices[0].message['content']

@dp.message()
async def handle(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
