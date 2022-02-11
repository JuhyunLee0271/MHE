from pykrx import stock
from datetime import datetime, timedelta
import time
import pandas as pd



class Scrapper:
    
    def __init__(self):
        self.code = stock.get_market_ticker_list(market="KOSPI") + stock.get_market_ticker_list(market="KOSDAQ")
        self.dict = {code: stock.get_market_ticker_name(code) for code in self.code}  # {'005930': '삼성전자', ... }    

    # 가장 최근 날짜의 거래 대금 상위 10개 
    def getOHLCV(self):
        today = datetime.now()
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
        
        return today.strftime("%Y-%m-%d"), result
        
        

if __name__ == "__main__":
    sc = Scrapper()
    sc.getOHLCV()
        
        

    


    
    
