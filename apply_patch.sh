sed -i '/@dp.message()/a \
@dp.channel_post()\
async def handle_channel_post(message: types.Message):\
    text = message.text or ""\
    if text.strip() == "":\
        return\
    reply, mood_score, attitude = await ask_gpt(text)\
    await message.answer(reply)\
' bot.py
