import telegram, time, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from pyowm import OWM
from stock_scrapper import Scrapper
import matplotlib.pyplot as plt


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

        stock_select_cb_handler = CallbackQueryHandler(self.stock_select_callback)
        self.dispatcher.add_handler(stock_select_cb_handler)

        weather_handler = CommandHandler('weather', self.weather)
        self.dispatcher.add_handler(weather_handler)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
            
    def stock(self, update, context):
        buttons = [
            [InlineKeyboardButton('1. 상위 10개 종목 조회', callback_data = 1)], 
            [InlineKeyboardButton('2. 선호 종목 시세 조회', callback_data = 2)], 
            [InlineKeyboardButton('3. 취소', callback_data = 3)]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)
        self.core.send_message(chat_id=CHAT_ID, text = '선택해주세요', reply_markup = reply_markup)
    
    def stock_select_callback(self, update, context):
        data = update.callback_query.data
        
        # 거래대금 상위 10개 종목의 OHLCV 
        if data == '1':
            date, text = self.scrapper.getOHLCV()
            
            self.core.edit_message_text(text = F"{date}\n거래 대금 상위 10개 종목", 
                                        chat_id = update.callback_query.message.chat_id,
                                        message_id = update.callback_query.message.message_id)
            self.core.send_message(text = F"{text}", chat_id = CHAT_ID)

        # 해당 종목의 60일간 추이
        elif data == '2':
            self.core.edit_message_text(text = "조회할 종목을 선택해주세요", 
                                        chat_id = update.callback_query.message.chat_id,
                                        message_id = update.callback_query.message.message_id)
            # 선호 종목
            buttons = []
            for i in range(len(self.scrapper.favorite)):
                buttons.append([InlineKeyboardButton(F"{i+1}. {self.scrapper.dict[self.scrapper.favorite[i]]}", callback_data = self.scrapper.favorite[i])])
            reply_markup = InlineKeyboardMarkup(buttons)
            self.core.send_message(chat_id=CHAT_ID, text = '종목을 선택 해주세요', reply_markup = reply_markup)            
        
        elif data == '3':
            self.core.edit_message_text(text = "취소합니다.", 
                                        chat_id = update.callback_query.message.chat_id,
                                        message_id = update.callback_query.message.message_id)
        
        # 선호 종목 시세 조회 
        else:
            self.scrapper.getTrend(self.scrapper.dict[data])
            if os.path.exists('result.png'):
                self.core.send_photo(chat_id = CHAT_ID, photo = open('result.png', 'rb'))
                os.remove('result.png')
            else:
                self.core.send_message(text = "Error!", chat_id = CHAT_ID)
        
        if data not in ['2','3']:
            self.stock(update, context)
            
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
    
    

