import telegram, time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, WebhookInfo
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler
from pyowm import OWM
from stock_scrapper import Scrapper

WEATHER_API_KEY = "cb7685dd2aef284e5946c10e5a3e559d"
with open('token_id.txt', 'rt') as f:
    text = f.readlines()
    TOKEN = str(text[0].split('=')[-1].strip('\n')[2:-1])
    CHAT_ID = str(text[1].split('=')[-1].strip('\n')[2:-1])

"""
1. 거래대금 상위 10개 종목의 OHLCV 조회
종목에 대한 
"""

class TelegramBot:
    def __init__(self):
        self.core = telegram.Bot(token=TOKEN)
        self.updater = Updater(token=TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.id = CHAT_ID
        self.scrapper = Scrapper()

        # Welcome Message
        self.core.send_message(chat_id = CHAT_ID, text="Hello! May I help you?")

        # Handler - (Command, Method) Binding
        stock_handler = CommandHandler('stock', self.stock)
        self.dispatcher.add_handler(stock_handler)

        call_back_handler = CallbackQueryHandler(self.callback_button)
        self.dispatcher.add_handler(call_back_handler)

        weather_handler = CommandHandler('weather', self.weather)
        self.dispatcher.add_handler(weather_handler)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
            
    def stock(self, update, context):
        buttons = [[
            InlineKeyboardButton('1. 종목 조회', callback_data=1),
            InlineKeyboardButton('2. 시세 조회', callback_data=2)
        ], [
            InlineKeyboardButton('3. 취소', callback_data=3)
        ]]

        reply_markup = InlineKeyboardMarkup(buttons)
        self.core.send_message(chat_id=CHAT_ID, text='선택해주세요', reply_markup = reply_markup)
    
    def callback_button(self, update, context):
        data = update.callback_query.data
        
        if data == '1':
            date, Top10 = self.scrapper.getOHLCV()
            text = ""
            for e in Top10:
                text += str(e[0]) + " " + str(e[1]) + " " + str(e[2]) + " " + str(e[3]) + ";"
            text = text.replace(';', '\n')

            self.core.edit_message_text(text = F"{date} - 거래 대금 상위 10개 종목", 
                                        chat_id = update.callback_query.message.chat_id,
                                        message_id = update.callback_query.message.message_id)
            self.core.send_message(text = F"{text}", chat_id = CHAT_ID)
                                        

        elif data == '2':
            pass
        elif data == '3':
            pass
        
    def weather(self, update, context):
        latitude = 37.3849391
        longitude = 126.642785
        
        # Weather Info API
        owm = OWM(WEATHER_API_KEY)
        manager = owm.weather_manager()
        observation = manager.weather_at_coords(latitude, longitude)
        
        location = F"{observation.location.country}/{observation.location.name}" #KR/INCHEON
        status = observation.weather.status
        temperature = observation.weather.temp['temp']
        humidity = observation.weather.humidity
        
        self.core.send_location(chat_id=CHAT_ID, longitude=longitude, latitude=latitude)
        self.core.send_message(chat_id=CHAT_ID, 
            text=F"Location: {location}" + "\n" + F"Description: {status}" + "\n" + F"Temperature: {str(round((temperature - 273.15),1)) + '℃' }" + "\n" + F"Humidity: {humidity}")
                
if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
    
    

