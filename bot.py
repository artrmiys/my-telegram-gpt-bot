import os
import asyncio
import openai
import random
from aiogram import Bot, Dispatcher, types, F

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()

SOURCES = [
    "https://arzamas.academy",
    "https://polka.academy",
    "https://postnauka.ru",
    "https://gorky.media",
    "https://prozhito.org",
    "https://www.culture.ru",
    "https://the-steppe.com",
    "https://knife.media",
    "https://syg.ma",
    "https://archi.ru",
    "https://moskvichmag.ru",
    "https://birdinflight.com",
    "https://plato.stanford.edu",
    "https://iep.utm.edu",
    "https://www.rep.routledge.com",
    "https://arthive.com",
    "https://artsandculture.google.com",
    "https://artchive.ru",
    "https://prozhito.org/page/archive",
    "https://ru.knowledgr.com",
    "https://biography.yandex",
    "https://paperpaper.ru",
]


async def mood_line(text):
    prompt = f"""
Проанализируй эмоциональный тон фразы:

"{text}"

Определи состояние говорящего и поставь оценку от 1 до 10.
Сформулируй короткую, колкую, уверенную фразу без мата.

Формат строго:
"<число>/10 — <фраза>"
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content.strip()


async def reference_lookup(text):
    prompt = f"""
Текст: "{text}"

Если в тексте нет культурных / исторических / географических / персональных ссылок,
верни: ПУСТО.

Если есть — дай:
ℹ️ очень короткую справку в 1 предложение.

Не используй Википедию.
Только смысл. Без воды.
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    summary = r.choices[0].message.content.strip()

    if summary.lower().startswith("пусто"):
        return ""

    link = random.choice(SOURCES)
    return f"{summary}\n🔗 {link}"


async def transcribe(file_id):
    file = await bot.get_file(file_id)
    temp = "voice.ogg"
    await bot.download_file(file.file_path, temp)

    with open(temp, "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)

    full = r.get("text", "").strip()
    words = full.split()
    short = " ".join(words[:6]) + "…" if len(words) > 6 else full
    return full, short


async def make_reply(full_text):
    mood = await mood_line(full_text)

    system_style = """
Ты — Ботэнский 🤖.
Стиль:
— уверенная расслабленная наглость
— тёплая колкость
— харизма, но без агрессии
— без мата
"""

    user_prompt = f"""
Сообщение: "{full_text}"

Ответ строго:

Ботэнский 🤖:
<2 строки реакции, можно эмодзи>
Оценка: {mood}
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_style},
            {"role": "user", "content": user_prompt}
        ]
    )

    reply = r.choices[0].message.content.strip()
    info = await reference_lookup(full_text)

    if info:
        reply += f"\n\n{info}"

    return reply


async def reply_text(full_text):
    return await make_reply(full_text)


async def reply_voice(full_text, short):
    return f"🎤 сказал: {short}\n\n{await make_reply(full_text)}"


@dp.message(F.text)
async def on_text(message: types.Message):
    await message.answer(await reply_text(message.text))


@dp.message(F.voice)
@dp.message(F.video_note)
async def on_voice(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    full, short = await transcribe(file_id)
    await message.answer(await reply_voice(full, short))


@dp.channel_post()
async def on_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    if message.text:
        await message.reply(await reply_text(message.text), disable_notification=True)
    elif message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        full, short = await transcribe(file_id)
        await message.reply(await reply_voice(full, short), disable_notification=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

