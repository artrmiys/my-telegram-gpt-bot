import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_KEY)

# ========= GPT ANSWER (TEXT) =========
async def ask_gpt(text):
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — мой дружбан. Отвечай коротко, живо, с чёрным юмором, "
                    "сарказмом, иногда чуть грубовато, но без крайностей. "
                    "Пиши как реальный человек, не бот. Смешно, но умно. "
                    "Если вопрос тупой — подшути. Если грусть — подбодри."
                )
            },
            {"role": "user", "content": text}
        ],
        temperature=1.1,
        max_tokens=350
    )
    return resp.choices[0].message.content

# ========= VOICE → TEXT (КРУЖКИ и голос) =========
async def transcribe(file_path):
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcript.text

# ========= TEXT MESSAGES =========
@dp.message()
async def on_message(message: types.Message):
    # Text
    if message.text:
        reply = await ask_gpt(message.text)
        await message.answer(reply)
        return

    # Voice / Round video / Audio note
    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        file = await bot.get_file(file_id)
        file_path = f"voice.ogg"
        await bot.download_file(file.file_path, file_path)

        text = await transcribe(file_path)
        reply = await ask_gpt(text)
        await message.answer(f"🎤 Расшифровал: {text}\n\n💬 {reply}")
        return

    # Otherwise ignore
    await message.answer("Я вижу что-то странное... Но пока не умею это читать 🙂")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
