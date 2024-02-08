import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class Screener:
    def __init__(self, path: str= None) -> None:
        self.tickers = self.__process_tickers(path)
        self.key = os.environ['FMP_KEY_2']
        self.base = "https://financialmodelingprep.com/api/v3/"
        self.previous = set()
        self.results = dict()
    
    def __read_json_file(self, file_path) -> dict[str:list]:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    
    def __process_tickers(self, path: str= None, tickers: dict[str:list] = None) -> dict[str:list]:
        t = self.__read_json_file(path)
        clean = {
                    'Japan': '.T',
                    'Canada': '.TO',
                    'Austria': '.VI',
                    'Belgium': '.BR',
                    'Estonia': '.TL',
                    'France': '.PA',
                    'Germany': '.DE',
                    'Greece': '.AT',
                    'Hungary': '.BD',
                    'Italy': '.MI',
                    'Latvia': '.RG',
                    'Lithuania': '.VS',
                    'Netherlands': '.AS',
                    'Poland': '.WS',
                    'Portugal': '.LS',
                    'Romania': '.RO',
                    'Finland': '.HE',
                    'Spain': '.MC',
                    'Sweden': '.ST',
                    'Switzerland': '.SW',
                    'United Kingdom': '.L',
                    'New Zealand': '.NZ',
                    'Czech Republic': '.PR',
                    'USA': ''}
        # for k, v in t.items():
        #     t[k] = [i.split(':')[1]+clean[k] for i in t[k]]
        
        return t
    
    def __has_dividends_or_buybacks(self, ticker: yf.Ticker) -> bool:
        has_dividends = ticker.dividends.sum() > 0
        if has_dividends:
            return True
        try:
            has_buybacks = ticker.quarterly_cashflow.loc['Repurchase Of Capital Stock'].sum() < 0
            return has_buybacks
        except:
            return False
        
    def __has_market_cap_less_than_ncav(self, ticker: yf.Ticker) -> bool:
        try:
            total_liabilities = ticker.quarterly_balance_sheet.loc['Total Liabilities Net Minority Interest'][0]
            current_assets = ticker.quarterly_balance_sheet.loc['Current Assets'][0]
            market_cap = ticker.info['marketCap']
            return market_cap <= (current_assets - total_liabilities)
        except:
            return False
    
    def __get_cashflow(self, ticker: str, span:int = 5) -> float:
        url = f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&apikey={self.key}&limit={span}'
        response = requests.get(url)
        return response.json()

    def __get_profile(self, ticker: str, span:int = 5) -> str:
        url = f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key}'
        response = requests.get(url)
        return response.json()
    
    def __screen_dividends_and_buybacks(self, ret_dict:dict[str:dict], debug:bool = False)->list[str]:   
        ctn = 0
        m = []
        for k, v in ret_dict.items():
            try:
                ctn +=1
                t = yf.Ticker(k)
                has_dividends_or_buybacks = self.__has_dividends_or_buybacks(t)
                if has_dividends_or_buybacks:
                    v["Has Dividends or Buybacks"] = True
                else:
                    m.append(k)
            except:
                m.append(k)

            # TODO: Remove b4 shipping
            percentage_completed = (ctn + 1) / len(ret_dict) * 100
            if percentage_completed % 5 == 0 and debug:
                print(f"Processing: {percentage_completed:.0f}% complete")
        
        return m
       
    def __screen_ncav(self, ret_dict:dict[str:dict])->list[str]:
        ctn = 0
        m = []
        for k, v in ret_dict.items():
            try:
                ctn +=1
                t = yf.Ticker(k)
                has_dividends_or_buybacks = self.__has_market_cap_less_than_ncav(t)
                if has_dividends_or_buybacks:
                    v["Market Cap <= NCAV"] = True
                else:
                    m.append(k)
            except:
                m.append(k)

            # TODO: Remove b4 shipping
            percentage_completed = (ctn + 1) / len(ret_dict) * 100
            if percentage_completed % 5 == 0:
                print(f"Processing: {percentage_completed:.0f}% complete")
        
        return m

    def __screen_net_debt(self, ret_dict:dict[str:dict]) -> list[str]:
        m = []
        for k, v in ret_dict.items(): # check "Net Debt".
            try:
                ticker = yf.Ticker(k)
                has_net_debt = ticker.quarterly_balance_sheet.loc['Net Debt'][0] > 0
                if has_net_debt:
                    v["Net Debt"] = True
                else:
                    m.append(k)
            except:
                try:
                    has_net_debt = ticker.quarterly_balance_sheet.loc["Total Debt"][0] > 0 
                    if has_net_debt:
                        v["Net Debt"] = True
                    else:
                        m.append(k)
                except:
                    m.append(k)
        
        return m

    def __screen_five_year_yield(self, ret_dict:dict[str:dict]) -> float:
        m = []
        for k, v in ret_dict.items():
            try:
                profile = self.__get_profile()[0]
                five_year_fcf_average = sum([i['freeCashFlow'] for i in self.__get_cashflow(k)])/5
                mkt_cap = profile['mktCap']
                v["Name"] = profile['companyName']
                v["HQ Location"] = profile['country']
                v['5Y average yield > 10%'] = round((five_year_fcf_average/mkt_cap)*100, 2)
            except:
                m.append(k)

    def run(self, debug: bool = False) -> None:
        start_time = datetime.now()
        ticker_arr = [item for sub in self.tickers.values() for item in sub]
        ret_dict = {i:{"Name":str, "HQ Location":str, "Has Dividends or Buybacks": bool, "Net Debt": float, "5Y average yield > 10%": bool, "Market Cap <= NCAV": bool} for i in ticker_arr}
        steps = ['check "Has Dividends"', 'check "Market Cap <= NCAV"', 'check "Net Debt"', 'check "5Y average yield > 10%"','check "whitelist country"']
        removal_matrix = [[] * len(steps)]
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[0]}.")
        removal_matrix[0] = self.__screen_dividends_and_buybacks(ret_dict)
        print(f"Time to check dividends: {datetime.now() - start_time}")
        for i in removal_matrix[0]:
            ret_dict.pop(i)
    
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[1]}.")
        start_market_cap = datetime.now()
        removal_matrix[1] = self.__screen_ncav(ret_dict)
        print(f"Time to check Market Cap <= NCAV: {datetime.now() - start_market_cap}")
        for i in removal_matrix[1]:
            ret_dict.pop(i)
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[2]}.")
        start_net_debt = datetime.now()
        removal_matrix[2] = self.__screen_net_debt(ret_dict)
        print(f"Time to check Net Debt: {datetime.now() - start_net_debt}")
        for i in removal_matrix[2]: # remove tickers without Positive "Net Debt".
            ret_dict.pop(i)
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[3]}.")
        start_fcf_time = datetime.now()
        removal_matrix[3] = self.__screen_five_year_yield(ret_dict)
        print(f"Time to check Net Debt: {datetime.now() - start_fcf_time}")
        for i in removal_matrix[3]:
            ret_dict.pop(i)
        
        self.results = ret_dict

        print(f"Total run time {start_time-datetime.now()}")
