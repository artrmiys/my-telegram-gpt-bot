import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
import openai
import random

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = Bot(TOKEN)
dp = Dispatcher()

openai.api_key = OPENAI_KEY

def random_rating():
    ratings = [
        "1/10 — как гвоздь без шляпки — и держишься, и не держишься.",
        "2/10 — звучишь как недоваренный пельмень.",
        "3/10 — могло быть хуже, но куда уж.",
        "4/10 — уныние, но со вкусом.",
        "5/10 — ровно, как бетонная стена.",
        "6/10 — жив, но не светишься.",
        "7/10 — бодрячком, почти человек-фейерверк.",
        "8/10 — уверенный красавчик, но без фанфар.",
        "9/10 — сияешь, но пальцем не показывай.",
        "10/10 — легенда местного разлива."
    ]
    return random.choice(ratings)

async def ask_gpt(full_text):
    if len(full_text) > 50:
        short = " ".join(full_text.split()[:4]) + "…"
    else:
        short = full_text

    mood = random_rating()

    prompt = f"""
Ты — Ботэнский 🤖.
Стиль: дерзкий, дружелюбно-грубый, черный юмор, **без мата**.

Формат ответа строго такой:
Ботэнский 🤖:
(2 строки реакции на смысл, шутка / уверенное подначивание)
Оценка: {mood}

Оригинал текста:
"{full_text}"

Суть для реакции: "{short}"
"""

    resp = openai.chat.completions.create(
        model="gpt-4o-mini",  # дешево + норм стиль
        messages=[{"role": "user", "content": prompt}]
    )

    return resp.choices[0].message.content.strip()

@dp.message(F.text)
async def reply_private(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)

@dp.channel_post(F.text)
async def reply_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    reply = await ask_gpt(message.text)
    await message.reply(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
