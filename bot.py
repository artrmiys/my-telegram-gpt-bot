import os
import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile
import openai

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = Bot(TOKEN)
dp = Dispatcher()

openai.api_key = OPENAI_KEY

def random_rating():
    ratings = [
        "1/10 — звучишь как чай из пакетика, который уже выжимали.",
        "2/10 — жив, но зря.",
        "3/10 — настроение «серый дождь и мокрые кроссы».",
        "4/10 — почти нормально, но грустно смотреть.",
        "5/10 — ровно, без качелей.",
        "6/10 — чуть луч света в тоске.",
        "7/10 — уверенно и с намёком на харизму.",
        "8/10 — почти сияешь.",
        "9/10 — звезда, но лежишь.",
        "10/10 — разъеб без мата."
    ]
    return random.choice(ratings)

async def ask_gpt(full_text):
    if len(full_text) > 60:
        short = " ".join(full_text.split()[:5]) + "…"
    else:
        short = full_text

    mood = random_rating()

    prompt = f"""
Ты — Ботэнский 🤖. 
Стиль: радостная наглость, уверенность, дерзкие подколы, чёрный юмор, но **без мата**.
Отвечай всегда в 2 строки, коротко и умно.

Формат:
Ботэнский 🤖:
<реакция, подкол, шутка, 1-2 строки>
Оценка: {mood}

Текст был:
"{full_text}"
Суть:
"{short}"
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()


async def transcribe(file_id):
    file = await bot.get_file(file_id)
    path = file.file_path
    local = "temp.ogg"
    await bot.download_file(path, local)

    with open(local, "rb") as audio:
        result = openai.Audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio
        )
    return result.text.strip()


# ==== ЛС текст ====
@dp.message(F.text)
async def reply_private(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)

# ==== ЛС кружок / голос ====
@dp.message(F.voice | F.video_note)
async def reply_private_audio(message: types.Message):
    text = await transcribe(message.voice.file_id if message.voice else message.video_note.file_id)
    reply = await ask_gpt(text)
    await message.answer(reply)

# ==== КАНАЛ текст (тихие тоже) ====
@dp.channel_post(F.text)
async def reply_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    reply = await ask_gpt(message.text)
    await message.reply(reply)

# ==== КАНАЛ кружок / голос ====
@dp.channel_post(F.voice | F.video_note)
async def reply_channel_audio(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    text = await transcribe(message.voice.file_id if message.voice else message.video_note.file_id)
    reply = await ask_gpt(text)
    await message.reply(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
