from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from .Sheet import Sheet
from .Utilities import process_tickers
import pandas as pd
import aiohttp
import asyncio
import os
import json

load_dotenv()

# Data needed:
#   - NCAV Ratio (2 API calls):
#       - market_cap (profile endpoint: https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key})
#       - current_assets (balance sheet endpoint: https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}')
#       - total_liabilities (balance sheet endpoint: https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}')
#   - EnterpriseValue by FreeCashFlow Ratio (2 API calls)
#       - enterprise_value (key metrics endpoint: https://financialmodelingprep.com/api/v3/key-metrics/AAPL?period=annual&apikey=c1d88fddc1ed1f9e664304c787b35bfd)
#       - cashflow (cashflow endpoint: https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=5&apikey={self.key})
#   - Tangible Book Value Ratio (1 API call)
#       - tangible_book_value (key metrics endpoint: https://financialmodelingprep.com/api/v3/key-metrics/AAPL?period=annual&apikey=c1d88fddc1ed1f9e664304c787b35bfd)
#       - market_cap
#   - P/E Ratio (1 API call)
#       - P/E Ratio (key metrics endpoint: https://financialmodelingprep.com/api/v3/key-metrics/AAPL?period=annual&apikey=c1d88fddc1ed1f9e664304c787b35bfd)
        

class AsyncScreener2:
    def __init__(self, ticker_path: str) -> None:
        self.tickers = process_tickers(ticker_path)
        self.key = os.environ['FMP_KEY']
        self.results = {}
        # {"TICKER":{"TBV Ratio":int, "EnterpriseValue/FreeCashFlow Ratio": int,"NCAV Ratio":int, "P/E Ratio": int }}
    
    async def __get_data(self, session: aiohttp.ClientSession, ticker: str) -> tuple:
        profile = await self.__get_profile(session, ticker)
        cashflow = await self.__get_cashflow(session, ticker)
        key_metrics = await self.__get_key_metrics(session, ticker)
        return profile, cashflow, key_metrics
    
    async def __get_key_metrics(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?period=annual&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_cashflow(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=5&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_profile(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass

    async def __handle_screener(self, tickers: list[str], debug: bool = False) -> None:
        if debug:
            print(f"{debug}/{len(self.tickers)} batches processed...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.__get_data(session, ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks)
            for ticker, (profile, cashflow, key_metrics) in zip(tickers, results):
                # check if pass TBV Ratio
                res = {"TBV Ratio":int, "EnterpriseValue/FreeCashFlow Ratio": int,"NCAV Ratio":int, "P/E Ratio": int, "isAdded":False}
                try:
                    tbv = key_metrics[0]['tangibleAssetValue'] + key_metrics[0]['intangiblesToTotalAssets']
                    mc = key_metrics[0]['marketCap']
                    tbv_ratio = mc/tbv
                    res["TBV Ratio"] = tbv_ratio
                    if tbv_ratio > 0 and tbv_ratio < 1:
                        res["isAdded"] = True
                except Exception as e:
                    pass
                    print(f"Issue with {ticker}")
                try:
                    pe_ratio = key_metrics[0]['peRatio']
                    res["P/E Ratio"] = pe_ratio
                    if pe_ratio > 1 and pe_ratio < 10:
                        res["isAdded"] = True
                except Exception as e:
                    pass
                    print(f"Issue with {ticker}")

                
                self.results[ticker] = res

    
    async def run_async(self, batch_size:int=100):
        tickers_arr = [i for sublist in self.tickers.values() for i in sublist]
        print(f"Screening {len(tickers_arr)} stocks...\n")
        d = 0
        for i in range(0, len(tickers_arr), batch_size):
            is_middle = i == len(tickers_arr)//2
            start = datetime.now()
            await self.__handle_screener(tickers=tickers_arr[i:i+batch_size], debug=d)
            d+=1
            sleep(61-(datetime.now()-start).seconds)
        print(f"{len(self.results)} stocks remaining after screening")