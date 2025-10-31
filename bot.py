import asyncio
import os
import openai
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ContentType

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
openai.api_key = os.getenv("OPENAI_KEY")

bot = Bot(TOKEN)
dp = Dispatcher()

def rate_mood(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["плохо","хуево","устал","груст","один","пусто"]):
        return "Настроение: болото 🐸 — ну бля, соберись."
    if any(w in t for w in ["норм","ладно","такое","ок"]):
        return "Настроение: так себе 😐 — жить можно, но слабовато."
    return "Настроение: огонь ⚡ — пылаешь, тигр."

async def ask_gpt(full_text):
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "Отвечай дерзко, коротко, с подъебом и теплом. В конце всегда добавляй: ботэнский 😈"},
            {"role": "user", "content": full_text}
        ],
        max_tokens=100,
        temperature=1.2
    )
    reply = resp.choices[0].message["content"].strip()
    words = reply.split()
    reply = " ".join(words[:9])
    return reply

async def handle_circle(message: types.Message):
    full_text = message.caption or "без текста"
    reply = await ask_gpt(full_text)
    mood = rate_mood(full_text)
    await bot.send_message(message.chat.id, f"{reply}\n\n{mood}", reply_to_message_id=message.message_id)

@dp.message(F.chat.type == "private")
async def private_chat(message: types.Message):
    if message.content_type == ContentType.VIDEO_NOTE:
        return await handle_circle(message)
    full_text = message.text
    reply = await ask_gpt(full_text)
    mood = rate_mood(full_text)
    await message.answer(f"{reply}\n\n{mood}")

@dp.channel_post()
async def channel_handler(message: types.Message):
    if message.content_type == ContentType.VIDEO_NOTE:
        return await handle_circle(message)

    full_text = message.text or message.caption
    if not full_text:
        return

    reply = await ask_gpt(full_text)
    mood = rate_mood(full_text)
    await bot.send_message(message.chat.id, f"{reply}\n\n{mood}", reply_to_message_id=message.message_id)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
