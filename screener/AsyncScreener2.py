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
    def __init__(self, ticker_path: str, sheet_path:str = "./service_account.json", sheet_name: str = "V2 Screener") -> None:
        """
        Initializes the AsyncScreener2 instance.

        Parameters:
        - `ticker_path` (str): Path to the file containing the tickers to be processed.
        - `sheet_path` (str): Path to the Google Sheets service account credentials file.
        - `sheet_name` (str): Name of the Google Sheet to use for storing results.

        Returns:
        - `None`
        """
        self.tickers = process_tickers(ticker_path)
        self.key = os.environ['FMP_KEY']
        self.industry_blacklist = ['Banks', 'Insurance']
        self.sheet_client = Sheet(sheet_path= sheet_path, file_name=sheet_name)
        self.results = dict()
        self.industry_blacklist_tickers = list()
        self.floats = None
        self.previous = self.sheet_client.get_all_previously_seen_tickers()
    
    def __remove_previously_seen(self) -> list[str]:
        """
        Removes tickers that have been previously seen in Google Sheets.

        Returns:
        - `None`
        """
        drop = [i for i in self.results.keys() if i in self.previous]
        for i in drop:
            try:
                self.results.pop(i)
            except:
                continue
        return drop
    
    async def __get_data(self, session: aiohttp.ClientSession, ticker: str) -> tuple:
        """
        Retrieves various financial data for a given ticker.

        Parameters:
        - `session` (aiohttp.ClientSession): The aiohttp session to use for making requests.
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `tuple`: A tuple containing the profile, key metrics TTM, balance sheet, and cash flow data.
        """
        profile = await self.__get_profile(session, ticker)
        key_metrics_ttm = await self.__get_key_metrics(session, ticker)
        balance_sheet = await self.__get_balance_sheet(session, ticker)
        cashflow = await self.__get_cashflow(session, ticker)
        return profile, key_metrics_ttm, balance_sheet, cashflow
    
    async def __get_balance_sheet(self, session: aiohttp.ClientSession, ticker: str) -> str:
        """
        Retrieves the balance sheet for a given ticker.

        Parameters:
        - `session` (aiohttp.ClientSession): The aiohttp session to use for making requests.
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `str`: The balance sheet data in JSON format.
        """
        async with session.get(f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_key_metrics(self, session: aiohttp.ClientSession, ticker: str) -> str:
        """
        Retrieves the key metrics TTM (Trailing Twelve Months) for a given ticker.

        Parameters:
        - `session` (aiohttp.ClientSession): The aiohttp session to use for making requests.
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `str`: The key metrics TTM data in JSON format.
        """
        async with session.get(f'https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?period=quarter&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_profile(self, session: aiohttp.ClientSession, ticker: str) -> str:
        """
        Retrieves the company profile for a given ticker.

        Parameters:
        - `session` (aiohttp.ClientSession): The aiohttp session to use for making requests.
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `str`: The company profile data in JSON format.
        """
        async with session.get(f'https://financialmodelingprep.com/api/v3/profile/{ticker}?period=quarter&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_cashflow(self, session: aiohttp.ClientSession, ticker: str) -> str:
        """
        Retrieves the cash flow statement for a given ticker.

        Parameters:
        - `session` (aiohttp.ClientSession): The aiohttp session to use for making requests.
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `str`: The cash flow data in JSON format.
        """
        async with session.get(f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=4&apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_floats(self) -> None:
        """
        Retrieves float data for all stocks.

        Returns:
        - `None`
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://financialmodelingprep.com/api/v4/shares_float/all?apikey={self.key}") as response:
                try:
                    self.floats = await response.json()
                except Exception as e:
                    print(f"Error fetching floats: {e}")
                    self.floats = None
            
    def __find_float_from_ticker(self, ticker) -> int:
        """
        Finds the float (outstanding shares) for a given ticker.

        Parameters:
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `int`: The number of outstanding shares, or 0 if not found.
        """
        for v in self.floats:
            if v['symbol'] == ticker:
                return v['outstandingShares']
        
        return 0 # if ticker can't be found, return 0
    
    
    async def __handle_screener2(self, tickers: list[str], debug: bool = False) -> None:
        """
        Handles the screening process for a batch of tickers.

        Parameters:
        - `tickers` (list[str]): A list of stock ticker symbols to screen.
        - `debug` (bool): If True, prints debug information. Default is False.

        Returns:
        - `None`
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.__get_data(session, ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks)
            for ticker, (profile, key_metrics_ttm, balance_sheet, cashflow) in zip(tickers, results):
                res = {"Name":str(),"NCAV Ratio":"N/A", "P/aFCF Ratio":"N/A", "EV/aFCF":"N/A", "P/TBV Ratio":"N/A", "isAdded": False}
                try:
                    current_assets = int(balance_sheet[0]["totalCurrentAssets"])
                    total_liabilities = int(balance_sheet[0]["totalLiabilities"])
                    market_cap = int(key_metrics_ttm[0]["marketCapTTM"])
                    ncav = current_assets - total_liabilities
                    ratio = round(market_cap / ncav, 1)
                    if ratio > 0 and ratio < 2.5:
                        res["isAdded"] = True
                        res["NCAV Ratio"] = ratio
                    
                    free_float = self.__find_float_from_ticker(ticker)
                    y_0_ttm = key_metrics_ttm[0]['freeCashFlowPerShareTTM'] * free_float
                    rest = [i['freeCashFlow'] for i in cashflow]
                    total = y_0_ttm + sum(rest)
                    five_year_fcf_average = total / 5 
                    pfcfRatio = market_cap/five_year_fcf_average
                    
                    res["P/aFCF Ratio"] = round(pfcfRatio, 1)
                    if pfcfRatio > 0 and pfcfRatio < 10:
                        res["isAdded"] = True
                    
                    ev = key_metrics_ttm[0]["enterpriseValueTTM"]
                    res["EV"] = round(ev, 1)
                    evFCF = ev/five_year_fcf_average
                    
                    if evFCF > 1 and evFCF < 5:
                        res["isAdded"] = True
                        res["EV/aFCF"] = round(evFCF, 1)
                    
                    pTBV = market_cap/key_metrics_ttm[0]['tangibleAssetValueTTM']
                    
                    if pTBV > 0 and pTBV < 1:
                        res["isAdded"] = True
                        res["P/TBV Ratio"] = round(pTBV, 1)
                    
                    for bli in self.industry_blacklist:
                        if bli in profile[0]['industry']:
                            self.industry_blacklist_tickers.append(ticker)
                    if profile[0]["country"] != "CN" and profile[0]["country"] != "HK":
                        res["Name"] = profile[0]["companyName"]
                        res["Country"] = profile[0]["country"]
                        self.results[ticker] = res
                except Exception as e:
                    pass

    
    def __check_pafcf(self, debug:bool=False) -> None:
        """
        Removes stocks from the results dictionary where the P/aFCF (Price-to-average-Free-Cash-Flow) ratio exceeds 10.

        Parameters:
        - `debug` (bool): If True, prints the number of stocks removed based on the P/aFCF ratio. Default is False.

        Returns:
        - `None`
        """
        bad_pe = [key for key, val in self.results.items() if val['P/aFCF Ratio'] > 10]
        for bad in bad_pe:
            self.results.pop(bad, None)
        if debug:
            print(f"{len(bad_pe)} removed for P/aFCF Ratio")


    def __clean_results(self, debug:bool=False) -> None:
        """
        Cleans the results dictionary by removing stocks that were not added based on screening criteria or that belong to blacklisted industries.

        Parameters:
        - `debug` (bool): If True, prints the number of stocks removed during the cleaning process. Default is False.

        Returns:
        - `None`
        """
        to_remove = [key for key, val in self.results.items() if not val["isAdded"]]
        for i in self.industry_blacklist_tickers:
            to_remove.append(i)
        for tr in to_remove:
            self.results.pop(tr, None)

    
    def __calculate_runtime(self, number_of_batches:int, batch_size:int) -> int:
        """
        Estimates the runtime for the screening process based on the number of batches and batch size.

        Parameters:
        - `number_of_batches` (int): The number of batches to process.
        - `batch_size` (int): The size of each batch.

        Returns:
        - `int`: The estimated runtime in minutes.
        """
        est_seconds = number_of_batches * 61
        minutes, seconds = divmod(est_seconds, 60)

        return minutes
    
    
    async def run_async(self, batch_size:int=100) -> None:
        """
        Runs the asynchronous screening process in batches.

        Parameters:
        - `batch_size` (int): The number of stocks to process in each batch. Default is 100.

        Returns:
        - `None`
        """
        print("Setting up the screener...")
        await self.__get_floats()
        tickers_arr = [i for sublist in self.tickers.values() for i in sublist]
        remaining = len(tickers_arr)
        print(f"Screening {remaining} stocks...\nEstimated run time: ~{self.__calculate_runtime(remaining//batch_size, batch_size)+1} minute(s)...\n")
        screened = 0
        b = 1
        tot = remaining//batch_size
        tot += 1
        sleep(61)
        for i in range(0, len(tickers_arr), batch_size):
            is_middle = i == len(tickers_arr)//2
            start = datetime.now()
            await self.__handle_screener2(tickers=tickers_arr[i:i+batch_size], debug=is_middle)
            screened+=len(tickers_arr[i:i+batch_size])
            remaining -= batch_size
            rem = 61-(datetime.now()-start).seconds
            if rem > 0 and b != tot:
                print(f"Batch {b}/{tot} complete. Waiting {rem} seconds for next batch (API limit reached).")
                sleep(rem)
                b+=1
            else:
                print(f"Batch {b}/{tot} complete.")
        
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
    
    def update_google_sheet(self, debug:bool=False) -> None:
        self.sheet_client.create_new_tab_v2()
        starting_size = len(self.results)
        self.__remove_previously_seen()
        cleaned = len(self.results)
        if debug:
            print(f"{starting_size - cleaned} tickers removed (previously present in google sheet).")
        
        self.sheet_client.add_row_data_v2(self.results)
        
        if debug:
            print("Google Sheet updated.")