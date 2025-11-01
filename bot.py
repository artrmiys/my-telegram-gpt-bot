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


# ---- Загрузка источников из файла ----
def load_sources():
    try:
        with open("sources.txt", "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except:
        return []

REFERENCE_SOURCES = load_sources()


# ---- Эмоциональный тон + оценка ----
async def mood_line(text):
    prompt = f"""
Проанализируй эмоциональный тон фразы:

"{text}"

Определи состояние говорящего и выставь оценку от 1 до 10.
Придумай колкую, слегка наглую, но добрую характеристику.
Без мата. Коротко.

Формат строго:
"<число>/10 — <фраза>"
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content.strip()


# ---- Поиск смысловых ссылок ----
async def reference_lookup(text):
    if not REFERENCE_SOURCES:
        return ""

    prompt = f"""
Текст: "{text}"

Если нет упоминаний культурных, исторических, географических или социальных объектов → верни ПУСТО.

Если есть → создай:
— супер краткую справку (одно предложение)
— выбери подходящую ссылку из списка:
{chr(10).join(REFERENCE_SOURCES)}

Формат:
ℹ️ <краткая справка>
🔗 <ссылка>

Коротко. Без воды. Не использовать Википедию.
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    result = r.choices[0].message.content.strip()
    if result.lower().startswith("пусто"):
        return ""
    return result


# ---- Распознавание аудио ----
async def transcribe(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "voice.ogg")

    with open("voice.ogg", "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)

    full = r.get("text", "").strip()
    words = full.split()
    short = " ".join(words[:5]) + "…" if len(words) > 5 else full
    return full, short


# ---- Формирование ответа ----
async def build_reply(full_text, show_short=None):
    mood = await mood_line(full_text)

    system_style = """
Ты — Ботэнский 🤖.
Стиль:
— уверенный
— тёплая наглость
— харизма ≠ токсичность
— слегка снисходительно, но по-дружески
— без мата
"""

    user_prompt = f"""
Фраза: "{full_text}"

Ответ строго по форме:

Ботэнский 🤖:
<2 строки эмоциональной, немного колкой реакции, можно эмодзи, можно анимированные эмоции типа 😏🤙✨🔥😎😌🤭🙂‍↔️🎭>
Оценка: {mood}
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_style},
            {"role": "user", "content": user_prompt}
        ]
    )

    answer = r.choices[0].message.content.strip()

    ref = await reference_lookup(full_text)
    if ref:
        answer += f"\n\n{ref}"

    if show_short:
        return f"🎤: {show_short}\n\n{answer}"

    return answer


# ---- Handlers ----
@dp.message(F.text)
async def on_text(message: types.Message):
    reply = await build_reply(message.text)
    await message.answer(reply)


@dp.message(F.voice)
@dp.message(F.video_note)
async def on_voice(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    full, short = await transcribe(file_id)
    reply = await build_reply(full, show_short=short)
    await message.answer(reply)


@dp.channel_post()
async def on_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    if message.text:
        reply = await build_reply(message.text)
        await message.reply(reply, disable_notification=True)
        return

    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        full, short = await transcribe(file_id)
        reply = await build_reply(full, show_short=short)
        await message.reply(reply, disable_notification=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
