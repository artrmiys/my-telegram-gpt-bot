import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram import F
from aiogram.types import Message

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

openai.api_key = OPENAI_KEY


async def ask_gpt(text):
    system_prompt = """
Ты — остроумный персонаж с лёгким нигилизмом и уличным юмором.
Всегда отвечаешь в 3 строки:

Ботэнский 🤖:
<реакция/мысль — коротко>
<панч/юмор>
Диагноз: <короткая оценка состояния говорящего — стёб, подкол>

Тон: дерзкий, уверенный, смешной. 
Не извиняешься, не объясняешься, не пишешь длинные лекции.
Если человек "раскис" — скажи это. Если орёт — скажи, что истерит.
Если голосовое-кружок — воспринимай как интимную исповедь.
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": text}
        ],
        temperature=1.35
    )

    reply = resp.choices[0].message["content"].strip()

    if not reply.startswith("Ботэнский"):
        reply = "Ботэнский 🤖:\n" + reply

    lines = reply.split("\n")
    reply = "\n".join(lines[:3])  # жёстко обрезаем до 3 строк

    return reply


@dp.message(F.text)
async def handle_text(message: types.Message):
    reply = await ask_gpt(message.text)
    await message.answer(reply)
    try:
        await bot.send_message(CHANNEL_ID, reply)
    except Exception as e:
        print('�� ���� ��������� � �����:', e)


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
