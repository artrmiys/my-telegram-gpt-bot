import fileinput

inserted = False

for line in fileinput.input("bot.py", inplace=True):
    print(line, end="")

    if "async def handle(message:" in line and not inserted:
        print("""
@dp.channel_post()  # ← Ловим посты в канале
async def handle_channel_post(message: types.Message):
    text = message.text or ""
    if text.strip() == "":
        return  # если пустой пост — игнорим
        
    reply, mood_score, attitude = await ask_gpt(text)

    # Отвечаем в том же канале
    await message.answer(reply)
""")
        inserted = True
