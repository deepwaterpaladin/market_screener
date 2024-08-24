from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from .Sheet import Sheet
from .Utilities import process_tickers
import pandas as pd
import aiohttp
import asyncio
import os

load_dotenv()

# calcs at issue:
#   - NCAV ratio [X]
#   - P/aFCF ratio [X]
#   - P/TBV ratio [ ]
#   - EV/aFCF ratio [X]

class AsyncScreener2:
    def __init__(self, ticker_path: str) -> None:
        self.tickers = process_tickers(ticker_path)
        self.key = os.environ['FMP_KEY']
        self.industry_blacklist = ['Banks', 'Insurance']
        self.results = dict()
        self.industry_blacklist_tickers = list()
        self.floats = None
    
    async def __get_data(self, session: aiohttp.ClientSession, ticker: str) -> tuple:
        profile = await self.__get_profile(session, ticker)
        key_metrics_ttm = await self.__get_key_metrics(session, ticker)
        balance_sheet = await self.__get_balance_sheet(session, ticker)
        cashflow = await self.__get_cashflow(session, ticker)
        return profile, key_metrics_ttm, balance_sheet, cashflow
    
    async def __get_balance_sheet(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_key_metrics(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?period=quarter&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_profile(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/profile/{ticker}?period=quarter&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_cashflow(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=4&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_floats(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://financialmodelingprep.com/api/v4/shares_float/all?apikey={self.key}") as response:
                try:
                    self.floats = await response.json()
                except Exception as e:
                    print(f"Error fetching floats: {e}")
                    self.floats = None
            
    def __find_float_from_ticker(self, ticker) -> int:
        for v in self.floats:
            if v['symbol'] == ticker:
                return v['outstandingShares']
        
        return 0 # if ticker can't be found, return 0
    
    
    async def __handle_screener2(self, tickers: list[str], debug: bool = False) -> None:
        async with aiohttp.ClientSession() as session:
            tasks = [self.__get_data(session, ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks)
            for ticker, (profile, key_metrics_ttm, balance_sheet, cashflow) in zip(tickers, results):
                res = {"Name":str(), "isAdded": False}
                try:
                    current_assets = int(balance_sheet[0]["totalCurrentAssets"])
                    total_liabilities = int(balance_sheet[0]["totalLiabilities"])
                    market_cap = int(key_metrics_ttm[0]["marketCapTTM"])
                    # market_cap = int(profile[0]["mktCap"])
                    ncav = current_assets - total_liabilities
                    ratio = round(market_cap / ncav, 2)
                    res["NCAV Ratio"] = ratio
                    if ratio > 0 and ratio < 2.5:
                        res["isAdded"] = True
                    
                    free_float = self.__find_float_from_ticker(ticker)
                    y_0_ttm = key_metrics_ttm[0]['freeCashFlowPerShareTTM'] * free_float
                    rest = [i['freeCashFlow'] for i in cashflow]
                    total = y_0_ttm + sum(rest)
                    five_year_fcf_average = total / 5 
                    pfcfRatio = market_cap/five_year_fcf_average
                    # res["Market Cap"] = market_cap
                    # res["Average Cashflow"] = round(five_year_fcf_average, 2)
                    res["P/aFCF Ratio"] = round(pfcfRatio, 2)
                    if pfcfRatio > 0 and pfcfRatio < 10:
                        res["isAdded"] = True
                    
                    ev = key_metrics_ttm[0]["enterpriseValueTTM"]
                    # res["EV"] = ev
                    evFCF = ev/five_year_fcf_average
                    res["EV/aFCF"] = round(evFCF, 2)
                    if evFCF > 1 and evFCF < 5:
                        res["isAdded"] = True
                    
                    tbv = key_metrics_ttm[0]['tangibleAssetValueTTM']
                    pTBV = market_cap/tbv
                    res["P/TBV Ratio"] = round(pTBV, 2)
                    if pTBV > 0 and pTBV < 1:
                        res["isAdded"] = True
                    
                    
                    isBlacklist = False
                    for bli in self.industry_blacklist:
                        if bli in profile[0]['industry']:
                            isBlacklist = True
                            self.industry_blacklist_tickers.append(ticker)
                    if profile[0]["country"] != "CN" and profile[0]["country"] != "HK":
                        res["Name"] = profile[0]["companyName"]
                        res["Country"] = profile[0]["country"]
                        self.results[ticker] = res
                except Exception as e:
                    pass

    
    def __check_pafcf(self, debug:bool=False) -> None:
        bad_pe = [key for key, val in self.results.items() if not (val['P/aFCF Ratio'] > 0 and val['P/aFCF Ratio'] < 10)]
        for bad in bad_pe:
            self.results.pop(bad, None)
        if debug:
            print(f"{len(bad_pe)} removed for P/aFCF Ratio")


    def __clean_results(self, debug:bool=False) -> None:
        to_remove = [key for key, val in self.results.items() if not val["isAdded"]]
        for tr in to_remove:
            self.results.pop(tr, None)

    
    def __calculate_runtime(self, number_of_batches:int, batch_size:int) -> int:
        est_seconds = number_of_batches * 61
        minutes, seconds = divmod(est_seconds, 60)

        return minutes
    
    
    async def run_async(self, batch_size:int=100) -> None:
        print("Setting up the screener...")
        tickers_arr = [i for sublist in self.tickers.values() for i in sublist]
        remaining = len(tickers_arr)
        screened = 0
        await self.__get_floats()
        sleep(59)
        print(f"Screening {remaining} stocks...\nEstimated run time: ~{self.__calculate_runtime(remaining//batch_size, batch_size)} minute(s)...\n")
        for i in range(0, len(tickers_arr), batch_size):
            is_middle = i == len(tickers_arr)//2
            start = datetime.now()
            await self.__handle_screener2(tickers=tickers_arr[i:i+batch_size], debug=is_middle)
            screened+=len(tickers_arr[i:i+batch_size])
            remaining -= batch_size
            rem = 61-(datetime.now()-start).seconds
            if rem > 0 and remaining < batch_size:
                sleep(rem)
        self.__clean_results()
        self.__check_pafcf(True)
        print(f"{screened} stocks screened.")
        print(f"{len(self.results)} stocks remaining after screening.")
    
    
    def create_xlsx(self, file_path:str) -> None:
        """
        Creates an Excel file with the screening results.

        Parameters:
        - `file_path` (str): The path to the Excel file.

        Returns:
        - `None`
        """
        if len(self.results) == 0:
            print(f'ERROR: results dictionary is empty. Execute `await AsyncScreener2.run_async()` to screen the stocks. If you are still seeing this after running `Screener.run()`, there are no new stocks from the previous execution.')
            return None
        df = pd.DataFrame.from_dict(self.results, orient='index')
        df.to_excel(file_path)
        print(f"File saved to {file_path}")