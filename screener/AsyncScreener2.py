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

class AsyncScreener2:
    def __init__(self, ticker_path: str) -> None:
        self.tickers = process_tickers(ticker_path)
        self.key = os.environ['FMP_KEY']
        self.industry_blacklist = ['Banks', 'Insurance']
        self.results = dict()
        self.industry_blacklist_tickers = list()
    
    async def __get_data(self, session: aiohttp.ClientSession, ticker: str) -> tuple:
        profile = await self.__get_profile(session, ticker)
        key_metrics = await self.__get_key_metrics(session, ticker)
        return profile, key_metrics
    
    async def __get_key_metrics(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?period=annual&apikey={self.key}') as response:
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
        # if debug:
        #     print(f"{debug}/{len(self.tickers)} batches processed...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.__get_data(session, ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks)
            for ticker, (profile, key_metrics) in zip(tickers, results):
                # check if pass TBV  & P/E Ratio
                res = {"TBV Ratio":0, "EnterpriseValue":0, "EnterpriseValue/FreeCashFlow Ratio": 0,"NCAV Ratio":0, "P/E Ratio": 0, "isAdded":False}
                try:
                    tbv = key_metrics[0]['tangibleAssetValue'] + key_metrics[0]['intangiblesToTotalAssets']
                    mc = key_metrics[0]['marketCap']
                    tbv_ratio = mc/tbv
                    res["TBV Ratio"] = tbv_ratio
                    pe_ratio = key_metrics[0]['peRatio']
                    res["P/E Ratio"] = pe_ratio
                    if (tbv_ratio >= 0.1 and tbv_ratio <= 0.9) and (pe_ratio > 1 and pe_ratio < 10):
                        res["isAdded"] = True
                    
                    # Calculate EV and FC
                    res["EnterpriseValue"] = key_metrics[0]['enterpriseValue']
                    res["EnterpriseValue/FreeCashFlow Ratio"] = key_metrics[0]['evToFreeCashFlow']
                    if res["EnterpriseValue/FreeCashFlow Ratio"] > 1 and res["EnterpriseValue/FreeCashFlow Ratio"] < 5:
                        res["isAdded"] = True

                    # Calculate NCAV
                    ncav = key_metrics[0]['netCurrentAssetValue']
                    res["NCAV Ratio"] = round(mc/ncav, 3)
                    if ncav > 0 and ncav < 2.5:
                        res["isAdded"] = True
                    
                    isBlacklist = False
                    for bli in self.industry_blacklist:
                        if bli in profile[0]['industry']:
                            isBlacklist = True
                            self.industry_blacklist_tickers.append(ticker)
                    if not isBlacklist:
                        self.results[ticker] = res
                except Exception as e:
                    pass

    def __check_pe(self, debug:bool=False) -> None:
        bad_pe = [key for key, val in self.results.items() if not (val['P/E Ratio'] > 0 and val['P/E Ratio'] < 10)]
        for bad in bad_pe:
            self.results.pop(bad, None)
        if debug:
            print(f"{len(bad_pe)} removed for P/E")


    def __clean_results(self, debug:bool=False) -> None:
        to_remove = [key for key, val in self.results.items() if not val["isAdded"]]
        for tr in to_remove:
            self.results.pop(tr, None)
        if debug:
            print(f"{len(to_remove)} removed for P/E")

    
    async def run_async(self, batch_size:int=150) -> None:
        tickers_arr = [i for sublist in self.tickers.values() for i in sublist]
        print(f"Screening {len(tickers_arr)} stocks...\nEstimated run time: ~{(len(tickers_arr)//batch_size)+2} minutes...\n")
        for i in range(0, len(tickers_arr), batch_size):
            is_middle = i == len(tickers_arr)//2
            start = datetime.now()
            await self.__handle_screener(tickers=tickers_arr[i:i+batch_size], debug=is_middle)
            rem = 61-(datetime.now()-start).seconds
            if rem > 0:
                sleep(rem)
        self.__check_pe(True)
        self.__clean_results()
        print(f"{len(self.results)} stocks remaining after screening")
    
    
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