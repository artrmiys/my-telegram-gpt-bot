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
    r = [
        "1/10 — выглядишь как унылый сырник.",
        "2/10 — жив, но на автопилоте.",
        "3/10 — будто батарейка на 5%.",
        "4/10 — можно лучше, но лень.",
        "5/10 — стабильно-посредственно.",
        "6/10 — почти живой человек.",
        "7/10 — приятный лучик тепла.",
        "8/10 — энерджайзер с харизмой.",
        "9/10 — ты сияешь как лампочка в подъезде.",
        "10/10 — легенда, икона, бог ракурсов."
    ]
    return random.choice(r)

async def transcribe(file_id):
    file = await bot.get_file(file_id)
    input_file = "input.ogg"
    output_file = "output.wav"
    await bot.download_file(file.file_path, input_file)

    os.system(f"ffmpeg -y -i {input_file} -ar 16000 -ac 1 {output_file} > /dev/null 2>&1")

    with open(output_file, "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)
    return r["text"].strip()

async def ask_gpt(full_text):
    short = " ".join(full_text.split()[:4]) + "…" if len(full_text) > 40 else full_text
    mood = random_rating()

    prompt = f"""
Ты — Ботэнский 🤖.
Стиль: добродушная наглость, немного грубый юмор, без мата, но смело.
Отвечай ровно в таком формате:

Ботэнский 🤖:
(короткая 1-2 строки реакция)
Оценка: {mood}

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
        fid = message.voice.file_id if message.voice else message.video_note.file_id
        text = await transcribe(fid)

    if not text:
        return

    reply = await ask_gpt(text)
    await message.reply(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
