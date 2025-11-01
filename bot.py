import os
import asyncio
import openai
from aiogram import Bot, Dispatcher, types, F

# --- ENV ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()


# ---- Загрузка источников для справок ----
def load_sources():
    try:
        with open("sources.txt", "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except:
        return []

REFERENCE_SOURCES = load_sources()


# ---- Распознавание голосовых / кружков ----
async def transcribe(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "voice.ogg")
    with open("voice.ogg", "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)
    full = r.get("text", "").strip()
    words = full.split()
    short = " ".join(words[:5]) + "…" if len(words) > 5 else full
    return full, short


# ---- Построение ответа ----
async def build_reply(text, show_short=None):
    prompt = f"""
Ты — Ботэнский 🤖.

Тон:
— уверенный
— слегка наглый, но по-доброму
— говоришь как человек, не как бот
— юмор без мата и токсичности
— коротко, метко, с харизмой

Источники (можно использовать только их, НЕ Википедию):
{chr(10).join(REFERENCE_SOURCES)}

Задача для текста: "{text}"

1) Определи настроение говорящего и поставь оценку.
   Формат: "<число>/10 — <короткая характеристика>"

2) Напиши **ровно 2 строки реакции**.  
   Хитро, уверенно, дружелюбно.  
   Можно использовать **1–3 аккуратных эмодзи**, никаких длинных цепочек.

3) Если видишь упоминание:
   — города
   — личности
   — культурной вещи
   — события
   Тогда добавь:
       ℹ️ <1 короткое объяснение>
       🔗 <ссылка из списка источников>
   Если нет → просто не добавляй.

Формат результата:

Ботэнский 🤖:
<строка 1>
<строка 2>
Оценка: <число>/10 — <характеристика>
<если есть>
ℹ️ <справка>
🔗 <ссылка>
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = r.choices[0].message.content.strip()

    # Для голосовых отображаем распознанный текст
    if show_short:
        return f"🎤 распознал как: {show_short}\n\n{answer}"
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

    if message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        full, short = await transcribe(file_id)
        reply = await build_reply(full, show_short=short)
        await message.reply(reply, disable_notification=True)
    else:
        reply = await build_reply(message.text)
        await message.reply(reply, disable_notification=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
