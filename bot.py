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


async def random_rating_gpt():
    base_scale = {
        1: "как будто ты выдохся морально",
        2: "живой, но без искры",
        3: "унылая солянка души",
        4: "нейтрально, без блеска",
        5: "стабильно, но без огонька",
        6: "есть жизнь в глазах",
        7: "приятное свечение",
        8: "солнечный зайчик человеческого вида",
        9: "прям сияешь",
        10: "бог ракурсов и харизмы"
    }

    score = random.randint(1, 10)
    meaning = base_scale[score]

    prompt = f"""
Сгенерируй новую формулировку оценки в стиле дружелюбной колкости.
Коротко, дерзко, но тепло. Без мата.
Формат: "{score}/10 — <фраза>"
Смысл основы: {meaning}
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return resp.choices[0].message.content.strip()


async def detect_reference(full_text):
    """
    Если в тексте есть историческое место, персонаж или закон —
    возвращаем справку.
    Иначе — пустую строку да.
    """
    prompt = f"""
Определи, есть ли в тексте значимая ссылка на:
— историческое место / здание
— страну / город
— закон, документ, реформу
— исторического или культурного персонажа

Текст: "{full_text}"

Если нет — верни ПУСТО.
Если есть — дай очень короткую справку (1–2 строки) + ссылку.
Формат:

ℹ️ <краткая суть>
🔗 <вики-ссылка>

Без лишних слов.
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    info = resp.choices[0].message.content.strip()

    if info.lower().startswith("нет") or info == "":
        return ""

    return info


async def transcribe(file_id):
    file = await bot.get_file(file_id)
    path = file.file_path
    temp = "voice.ogg"
    await bot.download_file(path, temp)

    with open(temp, "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)

    full = r.get("text", "").strip()
    words = full.split()
    short = " ".join(words[:6]) + "…" if len(words) > 6 else full
    return full, short


async def ask_gpt(full_text, short_text):
    mood = await random_rating_gpt()

    system_prompt = """
Ты — Ботэнский 🤖.
Стиль:
— умный
— слегка колкий, но добрый
— уверенный, не заискивающий
— говоришь легко, красиво, иногда с улыбкой снисходительности
— без мата и токсичности
"""

    user_prompt = f"""
Сообщение: "{full_text}"

Сформулируй ответ строго в формате:

Ботэнский 🤖:
(2 строки реакции с живой колкостью и теплотой, используй эмодзи)
Оценка: {mood}
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    answer = resp.choices[0].message.content.strip()

    reference = await detect_reference(full_text)
    if reference:
        answer += f"\n\n{reference}"

    return f"🎤 Распознал кружок как: {short_text}\n\n{answer}"


@dp.message(F.text)
async def reply_private(message: types.Message):
    reply = await ask_gpt(message.text, message.text)
    await message.answer(reply)


@dp.message(F.voice)
@dp.message(F.video_note)
async def reply_private_audio(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    full, short = await transcribe(file_id)
    reply = await ask_gpt(full, short)
    await message.answer(reply)


@dp.channel_post()
async def reply_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    if message.text:
        reply = await ask_gpt(message.text, message.text)
        await message.reply(reply, disable_notification=True)
        return

    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        full, short = await transcribe(file_id)
        reply = await ask_gpt(full, short)
        await message.reply(reply, disable_notification=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
