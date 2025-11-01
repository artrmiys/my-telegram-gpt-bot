import os
import asyncio
import openai
from base64 import b64encode
from aiogram import Bot, Dispatcher, types, F

# ─────────────────────────────────────────────────────────────
# ENV
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()

# ─────────────────────────────────────────────────────────────
# Источники (если не надо — оставь пустой файл)
def load_sources():
    try:
        with open("sources.txt", "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except:
        return []

REFERENCE_SOURCES = load_sources()

# ─────────────────────────────────────────────────────────────
# Распознавание аудио / кружков
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
# Генерация текста
async def build_reply(text, show_short=None):
    prompt = f"""
Ты — Ботэнский 🤖.
Стиль:
— уверенный
— чуть нагловатый, но добрый
— ироничный, но без токсичности
— без мата

Если можно — сделай вывод про настроение.

Источники (если найдёшь культурное/историческое упоминание — выбери подходящую ссылку):
{chr(10).join(REFERENCE_SOURCES)}

Формат строго:
Ботэнский 🤖:
<2 строки реакции>
Оценка: <число>/10 — <характеристика>
<если есть источник:>
ℹ️ <краткая инфа>
🔗 <ссылка>

Текст:
"{text}"
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = r.choices[0].message.content.strip()

    if show_short:
        return f"🎤 {show_short}\n\n{answer}"
    return answer

# ─────────────────────────────────────────────────────────────
# Описание фото через GPT-5-VISION
async def describe_image(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "image.jpg")

    with open("image.jpg", "rb") as f:
        img_b64 = b64encode(f.read()).decode("utf-8")

    prompt = """
Ты — Ботэнский 🤖.
Опиши фото через атмосферу и настроение присутствующих.
Не перечисляй объекты — передай ощущение.
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-vision",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{img_b64}"},
                    {"type": "input_text", "text": "Дай 2 строки описания + Оценка: <число>/10 — <характеристика>."}
                ]
            }
        ]
    )

    return r.choices[0].message.content.strip()

# ─────────────────────────────────────────────────────────────
# Handlers — личные сообщения
@dp.message(F.text)
async def on_text(message: types.Message):
    await message.answer(await build_reply(message.text))

@dp.message(F.voice)
@dp.message(F.video_note)
async def on_voice(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    full, short = await transcribe(file_id)
    await message.answer(await build_reply(full, show_short=short))

@dp.message(F.photo)
async def on_photo(message: types.Message):
    file_id = message.photo[-1].file_id
    await message.answer(await describe_image(file_id))

# ─────────────────────────────────────────────────────────────
# Handlers — канал
@dp.channel_post(F.text)
async def on_channel_text(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    await message.reply(await build_reply(message.text), disable_notification=True)

@dp.channel_post(F.photo)
async def on_channel_photo(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    file_id = message.photo[-1].file_id
    await message.reply(await describe_image(file_id), disable_notification=True)

# ─────────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
