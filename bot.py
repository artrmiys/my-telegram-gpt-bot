import os
import asyncio
import openai
from aiogram import Bot, Dispatcher, types, F

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()


def load_sources():
    try:
        with open("sources.txt", "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except:
        return []

REFERENCE_SOURCES = load_sources()


async def transcribe(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "voice.ogg")
    with open("voice.ogg", "rb") as f:
        r = openai.Audio.transcribe("whisper-1", f)
    full = r.get("text", "").strip()
    short = " ".join(full.split()[:5]) + "…" if len(full.split()) > 5 else full
    return full, short


async def build_reply(text, show_short=None):
    prompt = f"""
Ты — Ботэнский 🤖.  
Стиль общения:
— уверенный, чуть наглый, но добрый
— минимум воды
— лёгкая насмешка, но дружелюбная
— без мата

Источники для справок, если надо (не Википедия):
{chr(10).join(REFERENCE_SOURCES)}

Задача:
1) Проанализируй настроение текста.
2) Выдай оценку в формате "<число>/10 — краткая характеристика".
3) Напиши 2 строки живой реакции (можно эмодзи но редкие красивые).
4) Если в тексте упоминается место/культура/человек → дай краткую справку (до 1 предложения) + ссылку из списка выше.  
Если нет — пропусти блок справки.

Формат ответа строго:

Ботэнский 🤖:
<реакция в 2 строки>
Оценка: <число>/10 — <характеристика>
<если есть справка, то>
ℹ️ <краткая суть>
🔗 <ссылка>

Текст:
"{text}"
"""

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        temperature=0.9,
        messages=[{"role": "user", "content": prompt}]
    )

    answer = r.choices[0].message.content.strip()

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

    reply = await build_reply(message.text if message.text else "")
    await message.reply(reply, disable_notification=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
