import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from openai import OpenAI

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))  # -10019...

client = OpenAI(api_key=OPENAI_KEY)
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

def trim(text, max_words=6):
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + " ..."
    return text

async def ask_gpt(text):
    prompt = f"""
Ты — веселый, дерзкий, токсично-ласковый аналитик настроения.

Говоришь КОРОТКО: максимум 2 строки.
Если человек ныл — говори прямо: "братан, ты расклеился, соберись".
Если слишком радуется — подъеби чуть, приземли.
Всегда добавляй слово "ботэнский 😈" в конце.

Дай вывод в формате:
Комментарий + перенос строки
Оценка: (очень плохо / плохо / норм / хорошо / слишком радостный)

Текст:
{text}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

# --- ЛИЧКА ---
@dp.message(lambda m: m.chat.type == "private")
async def dm(message: types.Message):
    text = message.text or ""
    reply = await ask_gpt(trim(text))
    await message.answer(reply)

# --- КРУЖКИ ---
@dp.message(lambda m: m.voice or m.video_note)
async def voice(message: types.Message):
    reply = await ask_gpt("кружок пойман, анализирую вайб...")
    await message.answer(reply)

# --- ПОСТЫ В КАНАЛЕ (включая скрытые, без уведомлений, автоматические) ---
@dp.channel_post()
async def channel_post(message: types.Message):
    text = message.text or message.caption or ""
    if not text.strip():
        return
    reply = await ask_gpt(trim(text))

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=reply,
        reply_to_message_id=message.message_id
    )

async def main():
    print("Ботэнский взлетел 😈")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
