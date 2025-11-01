import fileinput

for line in fileinput.input("bot.py", inplace=True):
    # добавим импорт
    if line.startswith("from aiogram import"):
        print(line.rstrip())
        print("from aiogram.types import Message")
        continue

    # добавим получение channel_id
    if "OPENAI_KEY =" in line:
        print(line.rstrip())
        print("CHANNEL_ID = int(os.getenv('CHANNEL_ID'))")
        continue

    # там, где отправка пользователю -> дублируем в канал
    if "await message.answer(reply)" in line:
        print(line.rstrip())
        print("    try:")
        print("        await bot.send_message(CHANNEL_ID, reply)")
        print("    except Exception as e:")
        print("        print('Не смог отправить в канал:', e)")
        continue

    print(line, end="")
