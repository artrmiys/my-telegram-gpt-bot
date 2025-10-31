import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)
bot = Bot(TOKEN)
dp = Dispatcher()

STYLE_PROMPT = """
Ты отвечаешь с чёрным юмором, но умно и метко.
Ты не токсичный идиот, а **ироничный мудрец**, слегка обиженный жизнью.
Ты иногда можешь троллить, но дружелюбно.
Говоришь простым языком. Не длинно. Иногда с мем-референсами.
"""

async def ask_gpt(text):
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": STYLE_PROMPT},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

async def transcribe_voice(file_path):
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )
    return transcript.text

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Ну привет. Пиши. Или кружок кидай — разберём, что ты там шепчешь в микрофон ночью.")

@dp.message()
async def handle_message(message: types.Message):
    # Текст
    if message.text:
        reply = await ask_gpt(message.text)
        return await message.answer(reply)

    # Голос / кружок
    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        file = await bot.get_file(file_id)

        file_path = "voice.ogg"
        await bot.download_file(file.file_path, file_path)

        text = await transcribe_voice(file_path)
        reply = await ask_gpt(f"*Расшифровка кружка:*\n{text}")

        return await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
