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
        "1/10 — как чай из пакетика, который уже пять раз заваривали.",
        "2/10 — живёшь, но точнее — существуешь.",
        "3/10 — драма. Но без зрителей.",
        "4/10 — почти норм, но без искры.",
        "5/10 — ровно, но пресно.",
        "6/10 — слегка светишься.",
        "7/10 — уверенная стабильность.",
        "8/10 — приятный вайб.",
        "9/10 — почти легенда.",
        "10/10 — афиша на стену, кумир, икона."
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
Стиль: радостная уверенная наглость, добрые подколы, чёрный юмор, но **без мата**.
Отвечай в две строки.

Формат ответа:
Ботэнский 🤖:
<реакция, подкол с юмором>
Оценка: {mood}

Текст:
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

    # ✅ САМОЕ ВАЖНОЕ: правильный вызов
    with open(local, "rb") as audio:
        result = openai.Audio.transcribe(
            model="gpt-4o-mini-transcribe",
            file=audio
        )
    return result["text"].strip()

# ==== Личные сообщения: текст ====
@dp.message(F.text)
async def reply_private(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)

# ==== Личные сообщения: кружки и голосовые ====
@dp.message(F.voice | F.video_note)
async def reply_private_audio(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    text = await transcribe(file_id)
    reply = await ask_gpt(text)
    await message.answer(reply)

# ==== Канал: текст ====
@dp.channel_post(F.text)
async def reply_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    reply = await ask_gpt(message.text)
    await message.reply(reply)

# ==== Канал: кружки и голосовые ====
@dp.channel_post(F.voice | F.video_note)
async def reply_channel_audio(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    text = await transcribe(file_id)
    reply = await ask_gpt(text)
    await message.reply(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
