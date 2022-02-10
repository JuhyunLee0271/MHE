import telegram
from telegram.ext import Updater, MessageHandler, Filters

"""
# Bot name: stock-bot
# username: dev_jh_stock_bot
"""

with open('token&id.txt', 'rt') as f:
    text = f.readlines()
    TOKEN = str(text[0].split('=')[-1].strip('\n')[2:-1])
    CHAT_ID = str(text[1].split('=')[-1].strip('\n')[2:-1])

bot = telegram.Bot(token=TOKEN)

# updater
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher
updater.start_polling()

def handler(update, context):
    user_text = update.message.text
    if user_text == "안녕":
        bot.send_message(chat_id=CHAT_ID, text="안녕하세요, 반갑습니다")
    elif user_text == "뭐해":
        bot.send_message(chat_id=CHAT_ID, text="대화 중")

echo_handler = MessageHandler(Filters.text, handler)
dispatcher.add_handler(echo_handler)

