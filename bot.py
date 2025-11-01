import os
import asyncio
import base64
import openai
from aiogram import Bot, Dispatcher, types, F
import requests 
import csv
from datetime import datetime
from aiogram.filters import Command


# ─────────────────────────────────────────────────────────────
# ENV
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


openai.api_key = OPENAI_KEY
bot = Bot(TOKEN)
dp = Dispatcher()

def should_skip(text: str) -> bool:
    if not text:
        return False
    return "*бот не надо" in text.lower()

def log_message(user_id, msg_type, text):
    try:
        with open("logs.csv", "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(timespec='seconds'),
                user_id,
                msg_type,
                text.replace("\n", " ").strip()
            ])
    except Exception as e:
        print("Log error:", e)

def load_weekly_prompt():
    try:
        with open("weekly_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

WEEKLY_PROMPT = load_weekly_prompt()


# ─────────────────────────────────────────────────────────────
# Загружаем рекомендованные источники
def load_sources():
    try:
        with open("sources.txt", "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    except:
        return []

REFERENCE_SOURCES = load_sources()

def search_article(query):
    if not SERPAPI_KEY:
        return None

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "hl": "ru",
        "api_key": SERPAPI_KEY,
    }

    try:
        r = requests.get(url, params=params).json()
    except:
        return None

    results = r.get("organic_results", [])
    if not results:
        return None

    for item in results:
        link = item.get("link", "")
        if any(domain in link for domain in [
            "meduza.io", "gorky.media", "knife.media", "birdinflight.com",
            "arzamas.academy", "nplus1.ru", "disgustingmen.com"
        ]):
            return link

    return results[0].get("link", None)


# ─────────────────────────────────────────────────────────────
# Подгружаем system prompt из файла
def load_prompt():
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

BASE_PROMPT = load_prompt()

def load_voice_prompt():
    try:
        with open("prompt_voice.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""
VOICE_PROMPT = load_voice_prompt()


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

    sources = REFERENCE_SOURCES or []
    sources_list = "\n".join(f"• {s}" for s in sources) if sources else "—"

    article = search_article(text)  # ← ищем статью

    prompt = BASE_PROMPT.replace("{SOURCES}", sources_list)
    prompt = prompt.replace("{ARTICLE}", article if article else "")

    user_prompt = f"""
Сообщение:
\"\"\"{text}\"\"\"

Сформируй ответ строго по формату выше.
"""
    
    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_prompt}
        ],
    )

    ans = r.choices[0].message.content.strip()

    return f"🎤 {show_short}\n\n{ans}" if show_short else ans


async def build_voice_reply(text):

    if "*бот не надо" in text.lower():
        return None  # вообще ничего не отправляем

    article = search_article(text)
    sources = REFERENCE_SOURCES or []
    sources_list = "\n".join(f"• {s}" for s in sources) if sources else "—"

    prompt = VOICE_PROMPT.replace("{SOURCES}", sources_list)
    prompt = prompt.replace("{ARTICLE}", article if article else "")

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
    )

    return r.choices[0].message.content.strip()

async def build_weekly_summary():
    import pandas as pd

    if not os.path.exists("logs.csv"):
        return "Нет данных за неделю."

    try:
        df = pd.read_csv("logs.csv", header=None)
    except:
        return "Ошибка чтения лога."

    # Добавляем названия столбцов
    df.columns = ["timestamp", "user_id", "msg_type", "text"]

    # Преобразуем timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Фильтруем за неделю
    last_week = df[df["timestamp"] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]

    if last_week.empty:
        return "За неделю не было сообщений."

    text_block = "\n".join(last_week["text"].astype(str).tolist())

    r = openai.ChatCompletion.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": WEEKLY_PROMPT},
            {"role": "user", "content": f"Вот сообщения за неделю:\n\n{text_block}"}
        ]
    )

    return r.choices[0].message.content.strip()



# ─────────────────────────────────────────────────────────────
# 📷 Распознавание фото — через `gpt-4o` (рабочая vision модель)
async def describe_image(file_id):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, "image.jpg")

    with open("image.jpg", "rb") as f:
        img_bytes = f.read()

    b64 = base64.b64encode(img_bytes).decode("utf-8")

    r = openai.ChatCompletion.create(
        model="gpt-4o",  # рабочая модель с vision
        messages=[
            {"role": "system", "content": "Ты — Ботэнский 🤖. Отвечай уверенно, тепло но с иронией, без мата, но с  токсичностью, шутки и подколы."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Опиши атмосферу, эмоции людей и их отношение. Формат: Ботэнский 🤖: 2 строки реакции + строка Оценка <число>/10 — характеристика."
                    }
                ]
            }
        ]
    )

    return r.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# Команды в личке
@dp.message(Command("log"))
async def cmd_log(message: types.Message):
    if not os.path.exists("logs.csv"):
        await message.answer("Лог пока пуст 😐")
        return

    lines = []
    with open("logs.csv", "r", encoding="utf-8") as f:
        for row in f:
            parts = row.strip().split(",", 3)
            if len(parts) == 4:
                ts, uid, kind, text = parts
                lines.append(f"🕒 {ts}\n👤 {uid} | 🎙 {kind}\n{text}\n")

    logs_text = "\n".join(lines[-25:])  # последние 25 записей
    await message.answer(logs_text or "Лог пуст 😐")


@dp.channel_post(Command("log"))
async def cmd_channel_log(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    if not os.path.exists("logs.csv"):
        await message.reply("Лог пуст 😐", disable_notification=True)
        return

    lines = []
    with open("logs.csv", "r", encoding="utf-8") as f:
        for row in f:
            parts = row.strip().split(",", 3)
            if len(parts) == 4:
                ts, uid, kind, text = parts
                lines.append(f"🕒 {ts}\n👤 {uid} | 🎙 {kind}\n{text}\n")

    logs_text = "\n".join(lines[-25:])
    await message.reply(logs_text or "Лог пуст 😐", disable_notification=True)


# ─────────────────────────────────────────────────────────────
# Команды в канале
@dp.channel_post(Command("log"))
async def cmd_channel_log(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    if not os.path.exists("logs.csv"):
        await message.reply("Лог пуст 😐", disable_notification=True)
        return
    await message.reply_document(types.FSInputFile("logs.csv"), disable_notification=True)

@dp.channel_post(Command("weekly"))
async def cmd_channel_weekly(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    summary = await build_weekly_summary()
    await message.reply(summary, disable_notification=True)



# ─────────────────────────────────────────────────────────────
# Handlers в личке
@dp.message(F.text)
async def on_text(message: types.Message):
    if should_skip(message.text):
        return
    
    log_message(message.from_user.id, "text", message.text)
    reply = await build_reply(message.text)
    await message.answer(reply)


@dp.message(F.voice)
@dp.message(F.video_note)
async def on_voice(message: types.Message):
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    full, short = await transcribe(file_id)

    # стоп-фраза применяется к расшифровке речи
    if should_skip(full):
        return
    
    log_message(message.from_user.id, "voice", full)
    reply = await build_voice_reply(full)  # ← ВАЖНО: используем voice-промпт

    if reply:  # если None → ничего не отправляем
        await message.answer(reply)


@dp.message(F.photo)
async def on_photo(message: types.Message):
    # если есть подпись и там стоп — не отвечаем
    if message.caption and should_skip(message.caption):
        return

    log_message(message.from_user.id, "photo", message.caption or "")

    file_id = message.photo[-1].file_id
    reply = await describe_image(file_id)
    await message.answer(reply)


# ─────────────────────────────────────────────────────────────
# Handlers в канале

@dp.channel_post(F.text)
async def on_channel_text(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return
    
    if should_skip(message.text):
        return

    log_message(message.from_user.id if message.from_user else "channel", "text", message.text)

    reply = await build_reply(message.text)
    await message.reply(reply, disable_notification=True)


@dp.channel_post(F.voice)
@dp.channel_post(F.video_note)
async def on_channel_voice(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    full, short = await transcribe(file_id)

    if should_skip(full):
        return

    log_message(message.from_user.id if message.from_user else "channel", "voice", full)

    reply = await build_voice_reply(full)
    if reply:
        await message.reply(reply, disable_notification=True)


@dp.channel_post(F.photo)
async def on_channel_photo(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    if message.caption and should_skip(message.caption):
        return

    log_message(message.from_user.id if message.from_user else "channel", "photo", message.caption or "")

    file_id = message.photo[-1].file_id
    reply = await describe_image(file_id)
    await message.reply(reply, disable_notification=True)

# ─────────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
