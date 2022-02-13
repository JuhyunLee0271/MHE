from pykrx import stock
from datetime import datetime, timedelta
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates

class Scrapper:
    
    def __init__(self):
        self.code = stock.get_market_ticker_list(market="KOSPI") + stock.get_market_ticker_list(market="KOSDAQ")
        self.dict = {code: stock.get_market_ticker_name(code) for code in self.code}  # {'005930': '삼성전자', ... }    
        self.today = datetime.now()
        self.favorite = ['035420', '035720', '000660'] # NAVER, KAKAO, SKHynix

    # 가장 최근 날짜의 거래 대금 상위 10개 
    def getOHLCV(self):
        today = self.today
        while True:
            try:
                KOSPI = stock.get_market_ohlcv_by_ticker(today.strftime("%Y%m%d"), market="KOSPI")[['시가', '종가', '등락률', '거래대금']]
                time.sleep(1)
                KOSDAQ = stock.get_market_ohlcv_by_ticker(today.strftime("%Y%m%d"), market="KOSDAQ")[['시가', '종가', '등락률', '거래대금']]
                if len(KOSPI) > 0 and len(KOSDAQ) > 0:
                    break
            except:
                today -= timedelta(days=1)

        OHLCVs = pd.concat([KOSPI, KOSDAQ], axis=0, join='inner')
        OHLCVs.sort_values(by='거래대금', ascending=False, inplace=True)
        
        result = []

        for idx, row in OHLCVs[:10].iterrows():
            name = self.dict[row.name]
            open_price = int(row.시가)
            close_price = int(row.종가)
            fluctuate_rate = round(row.등락률,2)
            result.append((name, open_price, close_price, fluctuate_rate))
        
        text = ""
        for e in result:
            text += str(e[0]) + " " + str(e[1]) + " " + str(e[2]) + " " + str(e[3]) + ";"
        text = text.replace(';', '\n')

        return today.strftime("%Y-%m-%d"), text

    # 지난 60일간 추이 
    def getTrend(self, name):
        days = []
        startDate = self.today
        while len(days) < 60:
            if 0 <= startDate.weekday() <= 4:
                days.append(startDate.strftime("%Y%m%d"))
            startDate -= timedelta(1)
        days.reverse()
        
        code = ""

        for key, value in self.dict.items():
            if value == name:
                code = key
        
        if code:
            data = stock.get_market_ohlcv_by_date(days[0], days[-1], code)[['종가']]
            plt.plot(data.index, data.종가, color="red")
            plt.title(F"{name} 60일 시세 추이")
            plt.xlabel("날짜")
            plt.ylabel("종가")
            plt.savefig('result.png', dpi=200)
            plt.clf()
    
        else:
            return None

        
if __name__ == "__main__":
    sc = Scrapper()
    sc.getTrend("삼성전자")
        
