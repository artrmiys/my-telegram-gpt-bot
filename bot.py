import os
import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
import openai

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = Bot(TOKEN)
dp = Dispatcher()

openai.api_key = OPENAI_KEY

def random_rating():
    ratings = [
        "1/10 — звучишь как котлета, забытая в микроволновке.",
        "2/10 — жив, но без смысла, держись.",
        "3/10 — меланхолично, будто дождь по стеклу и ты — стекло.",
        "4/10 — серость, но стараешься, уважаю.",
        "5/10 — ровненько, как пол у строителя с лазерным уровнем.",
        "6/10 — уже почти человек, а не эмоция болота.",
        "7/10 — в тебе есть стиль, я вижу.",
        "8/10 — солнечные лучи пробили тучи депры.",
        "9/10 — харизма бьёт через края, стой смирно.",
        "10/10 — если бы бог был текстом — это был бы ты."
    ]
    return random.choice(ratings)

async def ask_gpt(full_text):
    # обрезаем текст для вывода, но анализируем оригинал
    if len(full_text) > 60:
        short = " ".join(full_text.split()[:5]) + "…"
    else:
        short = full_text

    mood = random_rating()

    prompt = f"""
Ты — Ботэнский 🤖. 
Стиль: радостная наглость, уверенность, дерзкие подколы, чёрный юмор, но **без мата**.
Отвечай всегда в 2 строки, коротко и умно.

Твой формат:
Ботэнский 🤖:
<шутка / реакция / подкол, 1-2 строки, живо>
Оценка: {mood}

Текст был такой:
"{full_text}"
Короткое ощущение:
"{short}"
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return resp.choices[0].message.content.strip()


# --- ЛС ---
@dp.message(F.text)
async def reply_private(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)

# --- КАНАЛ ---
@dp.channel_post(F.text)
async def reply_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    reply = await ask_gpt(message.text)
    await message.reply(reply)  # отвечает прямо под постом

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
