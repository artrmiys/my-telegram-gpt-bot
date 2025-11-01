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


async def rating_line(text):
    """
    Оценка не просто случайная — она учитывает "тон": усталость / возбуждение / задумчивость.
    """
    prompt = f"""
Проанализируй настроение фразы:

"{text}"

Выбери оценку от 1 до 10.
Затем придумай острую, но тёплую формулировку реакции.
Без мата. Стиль — дружелюбная наглая харизма.

Формат строго:
"<число>/10 — <короткая колкая фраза>"
"""

    r = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return r.choices[0].message.content.strip()


async def reference_check(text):
    """
    Ищем упоминания мест, событий, персон.
    Источник — не Википедия.
    """
    prompt = f"""
Текст: "{text}"

Есть ли здесь ссылка на:
— историческую личность
— город/место
— культурное явление
— закон/событие

Если нет → верни ПУСТО.

Если да → дай очень короткую справку (1–2 строки)
и ссылку не из Википедии (на сайт книг, статей, блогов, музеев, архивов).

Формат:
ℹ️ <краткая суть в одном предложении>
🔗 <ссылка>
"""

    r = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    result = r.choices[0].message.content.strip()
    if result.lower().startswith("пусто"):
        return ""
    return result


async def transcribe(file_id):
    file = await bot.get_file(file_id)
    temp = "voice.ogg"
    await bot.download_file(file.file_path, temp)

    with open(temp, "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)

    full = r.get("text", "").strip()
    short = " ".join(full.split()[:6]) + "…" if len(full.split()) > 6 else full
    return full, short


async def reply_builder(full_text, short):
    rating = await rating_line(full_text)

    system_style = """
Ты — Ботэнский 🤖.
Стиль:
— уверенный
— тёплая наглость
— самоирония и лёгкая насмешка, но по-доброму
— говоришь коротко и метко
— без мата
"""

    user_msg = f"""
Сообщение: "{full_text}"

Ответ пиши строго так:

Ботэнский 🤖:
<2 строки живой реакции, с харизмой, можно с эмодзи>
Оценка: {rating}
"""

    r = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_style},
            {"role": "user", "content": user_msg}
        ]
    )

    answer = r.choices[0].message.content.strip()

    ref = await reference_check(full_text)
    if ref:
        answer += f"\n\n{ref}"

    return f"🎤 распознал как: {short}\n\n{answer}"


@dp.message(F.text)
async def text_reply(message: types.Message):
    reply = await reply_builder(message.text, message.text)
    await message.answer(reply)


@dp.message(F.voice)
@dp.message(F.video_note)
async def voice_reply(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    full, short = await transcribe(file_id)
    reply = await reply_builder(full, short)
    await message.answer(reply)


@dp.channel_post()
async def channel_reply(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    if message.text:
        reply = await reply_builder(message.text, message.text)
        await message.reply(reply, disable_notification=True)
        return

    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        full, short = await transcribe(file_id)
        reply = await reply_builder(full, short)
        await message.reply(reply, disable_notification=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
