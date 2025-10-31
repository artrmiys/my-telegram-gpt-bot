import os
import asyncio
import random
import openai
from aiogram import Bot, Dispatcher, types, F

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()

def random_rating():
    ratings = [
        "1/10 — как будто ты выдохся морально.",
        "2/10 — живой, но без искры.",
        "3/10 — унылая солянка души.",
        "4/10 — нейтрально, но без блеска.",
        "5/10 — стабильно-неплохо.",
        "6/10 — есть жизнь в глазах.",
        "7/10 — приятный светящийся шарик.",
        "8/10 — солнечный зайчик человеческого вида.",
        "9/10 — прям сияешь.",
        "10/10 — ты просто бог ракурсов и харизмы."
    ]
    return random.choice(ratings)

async def transcribe(file_id):
    file = await bot.get_file(file_id)
    path = file.file_path
    temp = "voice.ogg"
    await bot.download_file(path, temp)

    with open(temp, "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)

    text = r.get("text", "").strip()
    return text if text else "..."

async def ask_gpt(full_text):
    short = " ".join(full_text.split()[:4]) + "…" if len(full_text) > 40 else full_text
    mood = random_rating()

    prompt = f"""
Ты — Ботэнский 🤖.
Стиль: жизнерадостный, немного наглый, добродушно-грубоватый, **без мата**, иногда чуть ниже пояса, но мило.

Отвечай всегда ровно так:

Ботэнский 🤖:
(2 строки остроумной реакции)
Оценка настроения: {mood}

Оригинал: "{short}"
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

@dp.message(F.text)
async def reply_private(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)

@dp.message(F.voice)
@dp.message(F.video_note)
async def reply_private_audio(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    text = await transcribe(file_id)
    reply = await ask_gpt(text)
    await message.answer(reply)

@dp.channel_post()
async def reply_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    text = None

    if message.text:
        text = message.text
    elif message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        text = await transcribe(file_id)

    if not text:
        return

    reply = await ask_gpt(text)
    await message.reply(reply, disable_notification=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
