import asyncio
import os
from openai import OpenAI
from aiogram import Bot, Dispatcher, types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_KEY)

async def ask_gpt(text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "Отвечай естественно, с характером и осмысленно."},
            {"role": "user", "content": text}
        ]
    )
    return resp.choices[0].message.content.strip()

@dp.channel_post()
async def handler(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    if not message.text:
        return

    reply = await ask_gpt(message.text)
    await message.reply(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
