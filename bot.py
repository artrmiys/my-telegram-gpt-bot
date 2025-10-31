import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
import openai

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

openai.api_key = OPENAI_KEY

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

def trim(text, max_words=6):
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + " ..."
    return text

async def ask_gpt(text):
    prompt = f"""
Ты — дерзкий, веселый и слегка токсичный друг.
Отвечаешь максимум в две строки.
В конце обязательно добавляешь "ботэнский 😈".

Также ставь оценку настроения:

- Если нытье → "Оценка: расклеился"
- Нейтрально → "Оценка: норм"
- Слишком радостный → "Оценка: слишком радуешься"
- Агрессивный → "Оценка: злой тигр"

Текст для анализа:
{text}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message["content"].strip()

# --- ЛИЧКА ---
@dp.message(lambda m: m.chat.type == "private")
async def private_handler(message: types.Message):
    text = message.text or ""
    reply = await ask_gpt(trim(text))
    await message.answer(reply)

# --- КРУЖОК / ВОЙС ---
@dp.message(lambda m: m.voice or m.video_note)
async def voice_handler(message: types.Message):
    reply = await ask_gpt("кружок. эмоции анализирую.")
    await message.answer(reply)

# --- КАНАЛ (включая скрытые / без звука) ---
@dp.channel_post()
async def channel_handler(message: types.Message):
    text = message.text or message.caption or ""
    if not text:
        return
    reply = await ask_gpt(trim(text))
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=reply,
        reply_to_message_id=message.message_id
    )

async def main():
    print("ботэнский взлетел 😈")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
