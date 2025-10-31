import asyncio
import os
import openai
from aiogram import Bot, Dispatcher, types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
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
    if message.chat.id != CHANNEL_ID:
        return
    if not message.text:
        return
    
    reply = await ask_gpt(message.text)
    await bot.send_message(CHANNEL_ID, reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
