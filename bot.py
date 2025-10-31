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
Ты — дерзкий, радостный и немного злой друг.
Отвечаешь в 2 строки, остро, уверенно, без воды.
Всегда заканчиваешь фразой: "ботэнский 😈"

После ответа пиши строку:
Оценка: расклеился / норм / слишком радуешься / злой тигр

Текст:
{text}
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message["content"].strip()

# Личка
@dp.message(lambda m: m.chat.type == "private")
async def private_message(message: types.Message):
    reply = await ask_gpt(trim(message.text or ""))
    await message.answer(reply)

# Кружок / войс
@dp.message(lambda m: m.voice or m.video_note)
async def voice_handler(message: types.Message):
    reply = await ask_gpt("кружок: распознать настроение")
    await message.answer(reply)

# Канал — включая скрытые/без уведомления
@dp.channel_post()
async def channel_post_handler(message: types.Message):
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
