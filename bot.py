import asyncio
import os
import tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import openai

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY

bot = Bot(TOKEN)
dp = Dispatcher()

STYLE_PROMPT = """
Ты отвечаешь с черным, но умным юмором.
Стиль: мудрый человек, который устал от всей этой хуйни, но все ещё почему-то жив.
Коротко. По делу. Иногда с принижением, но без злобы.
"""

async def ask_gpt(text):
    resp = openai.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": STYLE_PROMPT},
            {"role": "user", "content": text}
        ]
    )
    return resp.choices[0].message.content

async def transcribe_voice(file_path):
    with open(file_path, "rb") as f:
        r = openai.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )
    return r.text

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Ну давай. Пиши. Или кружок кидай. Я все слышу.")

@dp.message()
async def handle(message: types.Message):
    # Текст
    if message.text:
        reply = await ask_gpt(message.text)
        return await message.answer(reply)

    # Кружок / голос
    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        file = await bot.get_file(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
            await bot.download_file(file.file_path, tmp.name)
            text = await transcribe_voice(tmp.name)

        reply = await ask_gpt(f"Человек сказал в кружке:\n{text}")
        return await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
