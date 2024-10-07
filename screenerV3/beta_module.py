from dotenv import load_dotenv
from screener.Sheet import Sheet
from .utilities import Handler
import pandas as pd
from time import sleep
import aiohttp
import os
import json

load_dotenv()


class BetaModule:
    def __init__(self, ticker_path: str, sheet_path:str = "./service_account.json", sheet_name: str = "Screener") -> None:
        self.sheet_client = Sheet(sheet_path= sheet_path, file_name=sheet_name)
        self.handler = Handler()
        self.tickers = self.handler.process_tickers(self.sheet_client, ticker_path)
        self.profile_fstr_arr = self.__format_request_str(1000)
        self.hist_fstr_arr = self.__format_request_str(300)
        self.key = os.environ['FMP_KEY']
        self.results = {}
        self.floats = None
    
    def __get_ticker_count(self) -> int:
        num = 0
        for k, v in self.tickers.items():
            num += len(v)
        return num
    
    def __format_request_str(self, limit:int=300) -> str:
        """
        Formats the tickers into a single request string, limited by the specified number.

        Parameters:
        - `limit` (int): The maximum number of tickers to include in the request string.

        Returns:
        - `str`: A formatted string of tickers, separated by commas.
        """
        all_tickers = []
        for country, tickers in self.tickers.items():
            for ticker in tickers:
                all_tickers.append(ticker)

        request_strings = [
            ",".join(all_tickers[i:i + limit]) 
            for i in range(0, len(all_tickers), limit)
        ]
        
        return request_strings
    
    async def __get_profile(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_historical(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={self.key}') as response:
            try:
                return await response.json()# if response.status == 200 else print("Hit API limit. Waiting 55 seconds.") and sleep(55)
            except Exception as e:
                pass
    
    async def __get_balance_sheet(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}') as response:
            try:
                return await response.json()# if response.status == 200 else print("Hit API limit. Waiting 55 seconds.") and sleep(55)
            except Exception as e:
                pass
    
    async def __get_cashflow(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=5&apikey={self.key}') as response:
            try:
                return await response.json()# if response.status == 200 else print("Hit API limit. Waiting 55 seconds.") and sleep(55)
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
    
    def __check_reqs(self, requests_sent:int) -> None:
        if requests_sent % 299 == 0:
            print("Sleeping for 55 seconds to avoid hitting API limit.")
            sleep(55)
    
    def __clean_results(self, d:dict):
        ret = {}
        for k, v in d.items():
            try:
                if v["Net Debt"] > 0:
                    continue # screen out stocks with net debt
                elif v["isAdded"]:
                    ret[k] = v
            except:
                continue
        
        return ret
    
    async def run_async(self, debug:bool=False) -> dict:
        stk_res = {}
        blacklist = ["CN", "HK"]
        issues = []
        requests_sent = 0
        starting_stocks = self.__get_ticker_count()
        print(f"Screening {starting_stocks} stocks...")
        async with aiohttp.ClientSession() as session:
            for string in self.profile_fstr_arr:
                res = await self.__get_profile(session, string)
                requests_sent += 1
                if res is None:
                    continue
                for profile in res:
                    if int(profile['mktCap']) <= 0:
                        issues.append(profile['symbol'])
                        continue
                    if profile['country'] in blacklist:
                        issues.append(profile['symbol'])
                        continue
                    
                    try:
                        if profile['industry'][:5] == "Banks" or profile['industry'][:9] == "Insurance" or profile["industry"][:9] == "Financial" or profile['industry'][:10] == "Investment" or profile['industry'] == "Asset Management":
                            issues.append(profile['symbol'])
                            continue
    
                        div = float(profile.get("lastDiv", 0))
                    except (IndexError, ValueError, TypeError):
                        issues.append(profile['symbol'])
                        continue

                    stk_res[profile['symbol']] = {
                        "Name": profile["companyName"],
                        "Market Cap": profile['mktCap'],
                        "HQ Location": profile["country"],
                        "Exchange Location": profile["exchange"],
                        "Industry": profile["industry"]
                    }

            # get all balance sheet
            starting_stocks = starting_stocks-len(issues)
            print(f"Phase I complete.\n{len(issues)} stocks removed.\n{starting_stocks} remaining.") if debug else None
            issues = []
            for k, v in stk_res.items():
                self.__check_reqs(requests_sent)
                bs = await self.__get_balance_sheet(session, k)
                requests_sent += 1
                try: 
                    current_assets = int(bs[0]["totalCurrentAssets"])
                    total_liabilities = int(bs[0]["totalLiabilities"])
                    ncav = current_assets - total_liabilities
                    ratio = round(v["Market Cap"] / ncav, 1)
                    net_debt = int(bs[0]["netDebt"])
                    v["Net Debt"] = net_debt
                    if ratio > 0 and ratio < 2.5:
                        v["isAdded"] = True
                        v["NCAV Ratio"] = ratio

                except:
                    issues.append(k)
                    continue
            
            for i in issues:
                stk_res.pop(i)
            
            issues = []
            for k, v in stk_res.items():
                self.__check_reqs(requests_sent)
                km = await self.__get_key_metrics(session, k)
                requests_sent += 1
                cf = await self.__get_cashflow(session, k)
                requests_sent +=1
                try:
                    free_float = self.__find_float_from_ticker(k)
                    y_0_ttm = km[0]['freeCashFlowPerShareTTM'] * free_float
                    rest = [i['freeCashFlow'] for i in cf]
                    total = y_0_ttm + sum(rest)
                    five_year_fcf_average = total / 5 
                    pfcfRatio = v["Market Cap"]/five_year_fcf_average
                    
                    res["P/aFCF Ratio"] = round(pfcfRatio, 1)
                    if pfcfRatio > 0 and pfcfRatio < 10:
                        v["isAdded"] = True
                    
                    negCashflow = 0
                    for i in rest:
                        if i < 0:
                            negCashflow += 1
                    if negCashflow > 2:
                        continue
                    ev = km[0]["enterpriseValueTTM"]
                    v["EV"] = round(ev, 1)
                    evFCF = ev/five_year_fcf_average
                    
                    if evFCF > 1 and evFCF < 5:
                        v["isAdded"] = True
                        v["EV/aFCF"] = round(evFCF, 1)
                    
                    pTBV = v["Market Cap"]/km[0]['tangibleAssetValueTTM']
                    
                    if pTBV > 0 and pTBV < 1:
                        v["isAdded"] = True
                        v["P/TBV Ratio"] = round(pTBV, 1)
                except:
                    issues.append(k)
                    continue

            
            self.results = self.__clean_results(stk_res)
            return stk_res