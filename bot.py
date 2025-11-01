import os
import asyncio
import openai
from aiogram import Bot, Dispatcher, types, F

# ─────────────────────────────────────────────────────────────

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()

# ─────────────────────────────────────────────────────────────
# Загружаем список источников (не Википедия)

def load_sources():
    try:
        with open("sources.txt", "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except:
        return []

REFERENCE_SOURCES = load_sources()

# ─────────────────────────────────────────────────────────────
# Распознавание аудио и кружков

async def transcribe(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "voice.ogg")

    with open("voice.ogg", "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)

    full = r.get("text", "").strip()
    parts = full.split()
    short = " ".join(parts[:5]) + "…" if len(parts) > 5 else full
    return full, short

# ─────────────────────────────────────────────────────────────
# Общий обработчик текста

async def build_reply(text, show_short=None):
    prompt = f"""
Ты — Ботэнский 🤖.
Стиль: уверенный, дерзкая наглость, дружелюбная ирония, без мата.

Источники для справок, если нужно:
{chr(10).join(REFERENCE_SOURCES)}

Формат ответа:

Ботэнский 🤖:
<реакция в 2 строки>
Оценка: <число>/10 — <характеристика>
<если есть ссылка:>
ℹ️ <краткая инфа>
🔗 <ссылка>

Текст:
"{text}"
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    ans = r.choices[0].message.content.strip()

    if show_short:
        return f"🎤 {show_short}\n\n{ans}"
    return ans

# ─────────────────────────────────────────────────────────────
# 💥 Новое: распознавание изображений (GPT-5-VISION)

async def describe_image(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "image.jpg")

    with open("image.jpg", "rb") as f:
        img_bytes = f.read()

    response = openai.ChatCompletion.create(
        model="gpt-5-vision",
        messages=[
            {"role": "system", "content": "Ты — Ботэнский 🤖. Отвечай харизматично, мягко нагловато, но доброжелательно."},
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image": img_bytes},
                    {"type": "text", "text": "Опиши что на фото. Почувствуй настроение. Ответ: 2 строки + оценка (<число>/10 — характеристика)."}
                ]
            }
        ]
    )

    return response.choices[0].message.content.strip()

# ─────────────────────────────────────────────────────────────
# Handlers

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
    file_id = message.photo[-1].file_id  # самое лучшее качество
    reply = await describe_image(file_id)
    await message.answer(reply)

@dp.channel_post()
async def on_channel(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    reply = await build_reply(message.text if message.text else "")
    await message.reply(reply, disable_notification=True)

# ─────────────────────────────────────────────────────────────

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
