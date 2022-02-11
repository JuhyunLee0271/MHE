import telegram, time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler


API_KEY = "478279052ea6562636f94d63e0b3ccad"
"""
# Bot name: stock-bot
# username: dev_jh_stock_bot
"""

with open('token_id.txt', 'rt') as f:
    text = f.readlines()
    TOKEN = str(text[0].split('=')[-1].strip('\n')[2:-1])
    CHAT_ID = str(text[1].split('=')[-1].strip('\n')[2:-1])

class TelegramBot:
    def __init__(self):
        self.core = telegram.Bot(token=TOKEN)
        self.updater = Updater(token=TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.id = CHAT_ID

        # Welcome Message
        self.core.send_message(chat_id = CHAT_ID, text="I'm a bot. please talk to me!")

        # Handler - (Command, Method) Binding
        task_handler = CommandHandler('task', self.task)
        self.dispatcher.add_handler(task_handler)

        call_back_handler = CallbackQueryHandler(self.callback_button)
        self.dispatcher.add_handler(call_back_handler)

        weather_handler = CommandHandler('weather', self.weather)
        self.dispatcher.add_handler(weather_handler)
    
    def run(self):
        self.updater.start_polling()
        self.updater.idle()
            
    def task(self, update, context):
        buttons = [[
            InlineKeyboardButton('1. 네이버 뉴스', callback_data=1),
            InlineKeyboardButton('2. 직방 매물', callback_data=2)
        ], [
            InlineKeyboardButton('3. 취소', callback_data=3)
        ]]

        reply_markup = InlineKeyboardMarkup(buttons)
        self.core.send_message(chat_id=CHAT_ID, text='작업을 선택해주세요', reply_markup = reply_markup)
    
    def callback_button(self, update, context):
        data = update.callback_query.data
        self.core.send_chat_action(chat_id=CHAT_ID, action=ChatAction.TYPING)

        if data == '3':
            self.core.edit_message_text(text="작업이 취소되었습니다.", chat_id=CHAT_ID, message_id = update.callback_query.message_id)
        
        else:
            self.core.edit_message_text(text=F"{data} 작업이 진행 중입니다.", chat_id=CHAT_ID, message_id = update.callback_query.message_id)

            if data == '1':
                time.sleep(1)
                self.core.send_message(text="뉴스를 수집했습니다", chat_id=CHAT_ID)
            
            elif data == '2':
                time.sleep(1)
                self.core.send_message(text="매물을 수집했습니다", chat_id=CHAT_ID)
        
    def weather(self, update, context):
        longitude = 37.3849391
        latitude = 126.642785

        self.core.send_location(chat_id=CHAT_ID, longitude=longitude, latitude=latitude)

        


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
    
    

