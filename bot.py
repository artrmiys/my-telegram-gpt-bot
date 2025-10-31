import asyncio
import os
from aiogram import Bot, Dispatcher, types
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_KEY)

async def ask_gpt(text):
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Отвечай как реальный человек с чёрным юмором, дерзко, но умно."},
            {"role": "user", "content": text}
        ],
        temperature=1.1,
    )
    return resp.choices[0].message.content

async def transcribe(file_path):
    with open(file_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return result.text

@dp.message()
async def on_message(message: types.Message):

    if message.text:
        reply = await ask_gpt(message.text)
        await message.answer(reply)
        return

    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        file = await bot.get_file(file_id)
        file_path = "voice.ogg"
        await bot.download_file(file.file_path, file_path)

        text = await transcribe(file_path)
        reply = await ask_gpt(text)
        await message.answer(f"🎤 {text}\n\n💬 {reply}")
        return

    await message.answer("не знаю что это, но я смотрю на это с подозрением 😐")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
