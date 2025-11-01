import os
import asyncio
import base64
import openai
from aiogram import Bot, Dispatcher, types, F

# ─────────────────────────────────────────────────────────────
# ENV
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()

# ─────────────────────────────────────────────────────────────
# Загружаем рекомендованные источники
def load_sources():
    try:
        with open("sources.txt", "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except:
        return []

REFERENCE_SOURCES = load_sources()

# ─────────────────────────────────────────────────────────────
# Распознавание аудио / кружков → Whisper
async def transcribe(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "voice.ogg")

    with open("voice.ogg", "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)

    full = r.get("text", "").strip()
    words = full.split()
    short = " ".join(words[:5]) + "…" if len(words) > 5 else full
    return full, short


# ─────────────────────────────────────────────────────────────
# Формирование реакции на текст
async def build_reply(text, show_short=None):
    prompt = f"""
Ты — Ботэнский 🤖.

Стиль ответа:
— уверенный, умная нагловатость
— дружелюбная ирония
— без мата
— 2 строки реакции, живые, но без шуток "про попугая".

Источники (если нужно дать справку, не использовать Википедию):
{chr(10).join(REFERENCE_SOURCES)}

Формат ответа:
Ботэнский 🤖:
<реакция 2 строки>
Оценка: <число>/10 — <характеристика>
<если нужна справка:>
ℹ️ <факт в одно предложение>
🔗 <ссылка>

Текст:
\"{text}\"
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    ans = r.choices[0].message.content.strip()

    return f"🎤 {show_short}\n\n{ans}" if show_short else ans


# ─────────────────────────────────────────────────────────────
# 📷 Распознавание фото — через `gpt-4o` (рабочая vision модель)
async def describe_image(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "image.jpg")

    with open("image.jpg", "rb") as f:
        img_bytes = f.read()

    b64 = base64.b64encode(img_bytes).decode("utf-8")

    r = openai.ChatCompletion.create(
        model="gpt-4o",  # ← Рабочая модель с изображениями
        messages=[
            {"role": "system", "content": "Ты — Ботэнский 🤖. Отвечай с умной улыбкой, тепло, без мата."},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"},
                    {"type": "text", "text": "Опиши кто на фото, настроение и динамику между людьми. Формат: 2 строки + оценка <число>/10 — характеристика."}
                ]
            }
        ]
    )

    return r.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────
# Handlers в личке
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

@dp.message(F.photo)
async def on_photo(message: types.Message):
    file_id = message.photo[-1].file_id
    reply = await describe_image(file_id)
    await message.answer(reply)


# ─────────────────────────────────────────────────────────────
# Handlers в канале
@dp.channel_post()
async def on_channel_text(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    if message.text:
        reply = await build_reply(message.text)
        await message.reply(reply, disable_notification=True)

@dp.channel_post(F.photo)
async def on_channel_photo(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    file_id = message.photo[-1].file_id
    reply = await describe_image(file_id)
    await message.reply(reply, disable_notification=True)


# ─────────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
