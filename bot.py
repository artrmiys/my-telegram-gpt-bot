import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram import F

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

openai.api_key = OPENAI_KEY


async def ask_gpt(text):
    system_prompt = """
Ты — дерзкий, уверенный, с чёрным юмором.
Каждый ответ ДОЛЖЕН начинаться с строки: "Ботэнский 🤖:"
Не извиняешься, не стесняешься, не пишешь формально.
Пиши разговорами, как в баре ночью.
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": text}
        ],
        temperature=1.2
    )

    answer = resp.choices[0].message["content"].strip()
    if not answer.startswith("Ботэнский"):
        answer = "Ботэнский 🤖: " + answer
    return answer


@dp.message(F.text)
async def handle_text(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)


@dp.message(F.video_note)
async def handle_circle(message: types.Message):
    file = await bot.get_file(message.video_note.file_id)
    data = await bot.download_file(file.file_path)

    path = "voice.ogg"
    with open(path, "wb") as f:
        f.write(data.read())

    transcript = openai.Audio.transcribe("whisper-1", open(path, "rb"))
    text = transcript["text"].strip()

    reply = await ask_gpt(text)
    await message.answer(f"🎤 Распознал кружок как: <i>{text}</i>\n\n{reply}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
