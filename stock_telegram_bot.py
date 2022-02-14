from cv2 import log
import telegram, time, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from pyowm import OWM
from stock_scrapper import Stock
from weather_scrapper import Weather
import matplotlib.pyplot as plt

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

        self.stock_scrapper = Stock()
        self.weather_scrapper = Weather()

        # Welcome Message
        self.core.send_message(chat_id=CHAT_ID, text = '안녕하세요, 무엇을 도와 드릴까요? (/hi)')

        # Handler - (Command, Method) Binding
        initial_handler = CommandHandler('hi', self.initial_option)
        self.dispatcher.add_handler(initial_handler)

        cb_select_handler = CallbackQueryHandler(self.callback_select)
        self.dispatcher.add_handler(cb_select_handler)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
    
    def initial_option(self, update, context):
        buttons = [
            [InlineKeyboardButton('1. 주식 조회', callback_data = 'stock')],
            [InlineKeyboardButton('2. 날씨 조회', callback_data = 'weather')]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)
        self.core.send_message(chat_id=CHAT_ID, text = '선택 해주세요', reply_markup = reply_markup)

    def stock(self, update, context):
        buttons = [
            [InlineKeyboardButton('1. 상위 10개 종목 조회', callback_data = 'stock_1')], 
            [InlineKeyboardButton('2. 선호 종목 시세 조회', callback_data = 'stock_2')], 
            [InlineKeyboardButton('3. 취소', callback_data = 'stock_3')]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)
        self.core.send_message(chat_id=CHAT_ID, text = '선택 해주세요', reply_markup = reply_markup)
    
    def callback_select(self, update, context):
        data = update.callback_query.data
        
        if data == 'stock':
            self.stock(update, context)
            return
        
        elif data == 'weather':
            self.weather(update, context)
            return

        # 거래대금 상위 10개 종목의 OHLCV 
        if data == 'stock_1':
            date, text = self.stock_scrapper.getOHLCV()
            
            self.core.edit_message_text(text = F"{date}\n거래 대금 상위 10개 종목", 
                                        chat_id = update.callback_query.message.chat_id,
                                        message_id = update.callback_query.message.message_id)
            self.core.send_message(text = F"{text}", chat_id = CHAT_ID)

        # 해당 종목의 60일간 추이
        elif data == 'stock_2':
            self.core.edit_message_text(text = "조회할 종목을 선택해주세요", 
                                        chat_id = update.callback_query.message.chat_id,
                                        message_id = update.callback_query.message.message_id)
            # 선호 종목
            buttons = []
            for i in range(len(self.stock_scrapper.favorite)):
                buttons.append([InlineKeyboardButton(F"{i+1}. {self.stock_scrapper.dict[self.stock_scrapper.favorite[i]]}", 
                                                    callback_data = self.stock_scrapper.favorite[i])])
            reply_markup = InlineKeyboardMarkup(buttons)
            self.core.send_message(chat_id=CHAT_ID, text = '종목을 선택 해주세요', reply_markup = reply_markup)            
            return
        
        elif data == 'stock_3':
            self.core.edit_message_text(text = "취소합니다.", 
                                        chat_id = update.callback_query.message.chat_id,
                                        message_id = update.callback_query.message.message_id)
        
        # 선호 종목 시세 조회 
        elif data in self.stock_scrapper.favorite:
            self.stock_scrapper.getTrend(self.stock_scrapper.dict[data])
            if os.path.exists('result.png'):
                self.core.send_photo(chat_id = CHAT_ID, photo = open('result.png', 'rb'))
                os.remove('result.png')
            else:
                self.core.send_message(text = "Error!", chat_id = CHAT_ID)
        
        # 위치별 날짜 조회 
        elif data in list(self.weather_scrapper.dict.keys()):
            location, status, temperature, humidity, latitude, longitude = self.weather_scrapper.getWeatherByCoords(data)
            self.core.send_location(chat_id=CHAT_ID, latitude=latitude, longitude=longitude)
            self.core.send_message(chat_id=CHAT_ID,
                                    text=F"Location: {location}" + "\n" + F"Description: {status}" + "\n" + F"Temperature: {str(round((temperature - 273.15),1)) + '℃' }" + "\n" + F"Humidity: {humidity}")
        
        self.initial_option(update, context)
            
    def weather(self, update, context):
        buttons = []
        for i in range(len(self.weather_scrapper.dict)):
            buttons.append([InlineKeyboardButton(F"{i+1}. {list(self.weather_scrapper.dict.keys())[i]}", 
                                                callback_data=list(self.weather_scrapper.dict.keys())[i])])
        reply_markup = InlineKeyboardMarkup(buttons)
        self.core.send_message(chat_id=CHAT_ID, text = '위치를 선택 해주세요', reply_markup = reply_markup)
    
    
                
if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()