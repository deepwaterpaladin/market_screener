from dotenv import load_dotenv
from screener.Sheet import Sheet
import pandas as pd
from time import sleep
import aiohttp
import asyncio
import os
import json

load_dotenv()

class AlphaModule:
    def __init__(self, ticker_path: str, sheet_path:str = "./service_account.json", sheet_name: str = "Screener") -> None:
        self.tickers = self.__process_tickers(ticker_path)
        self.profile_fstr_arr = self.__format_request_str(1000)
        self.hist_fstr_arr = self.__format_request_str(300)
        self.key = os.environ['FMP_KEY']
        self.sheet_client = Sheet(sheet_path= sheet_path, file_name=sheet_name)
        self.results = {}


    def __read_json_file(self, file_path) -> dict[str:list]:
        """
        Reads a JSON file and returns its content as a dictionary.

        Parameters:
        - `file_path` (str): The path to the JSON file.

        Returns:
        - `dict`: A dictionary containing the content of the JSON file.
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data


    def __process_tickers(self, path: str = None, tickers: dict[str:list] = None) -> dict[str:list]:
        """
        Processes tickers from a JSON file.

        Parameters:
        - `path` (str): The path to the JSON file containing stock tickers. Defaults to None.
        - `tickers` (dict): A dictionary of tickers. Defaults to None.

        Returns:
        - `dict`: A dictionary containing processed tickers.
        """
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

        return t


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
    
    def __check_reqs(self, requests_sent:int) -> None:
        if requests_sent % 299 == 0:
            print("Sleeping for 55 seconds to avoid hitting API limit")
            sleep(55)
    
    async def __get_profile(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_historical(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def __get_balance_sheet(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}') as response:
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
    
    async def run_async(self):
        # get all profiles
        # screen out any stocks without divs or buybacks
        # screen out any Chinese, Hong Kong, or Macau based companies/stocks.
        # screen out any stocks with market cap <= 0
        # create new list of stocks to performe remaining screening on

        stk_res = {}
        blacklist = ["CN", "HK"]
        issues = []
        requests_sent = 0
        stocks_added = 0
        async with aiohttp.ClientSession() as session: 
            for string in self.profile_fstr_arr:
                res = await self.__get_profile(session, string)
                requests_sent += 1
                if res is None:
                    continue
                for profile in res:
                    if int(profile['mktCap']) <= 0:
                        print(f"removing for: Market Cap")
                        issues.append(profile['symbol'])
                        continue
                    if profile['country'] in blacklist:
                        print(f"removing for: BL")
                        issues.append(profile['symbol'])
                        continue
                    try:
                        # Attempt to get the dividend value
                        div = float(profile.get("lastDiv", 0))
                    except (IndexError, ValueError, TypeError):
                        print(f"removing for: ERROR")
                        issues.append(profile['symbol'])
                        continue

                    stk_res[profile['symbol']] = {
                        "Name": profile["companyName"],
                        "Market Cap": profile['mktCap'],
                        "HQ Location": profile["country"],
                        "Exchange Location": profile["exchange"],
                        "Industry": profile["industry"],
                        "Has Dividends or Buybacks":div 
                    }
                    stocks_added += 1

            # get all cashflow
            print(f"Phase I complete.\n{len(issues)} stocks removed")
            issues = []
            for k, v in stk_res.items():
                self.__check_reqs(requests_sent)
                cf = await self.__get_cashflow(session, k)
                requests_sent += 1
                try:
                    if v['Has Dividends or Buybacks'] < 1:
                        buyback = sum([i["commonStockRepurchased"]
                                      for i in cf])
                        if buyback < 0:
                            v['Has Dividends or Buybacks'] = buyback
                    five_year_fcf_average = sum(
                        [i['freeCashFlow'] for i in cf])/5
                    average_yield = round(
                        (five_year_fcf_average/v['Market Cap'])*100, 2)
                    if average_yield < 10:
                        print(f"removing for: AVG YIELD")
                        issues.append(k)
                        continue
                    v['5Y average yield > 10%'] = average_yield
                    v['5Y average'] = five_year_fcf_average
                    v["Cash & Equivalents"]= cf[0]["cashAtEndOfPeriod"]

                except Exception as ex:
                    issues.append(k)
                    print(f"removing for: {ex}")
                    continue
            for i in issues:
                stk_res.pop(i)
            
            
            # get all balencesheets
            print(f"Phase II complete.\n{len(issues)} stocks removed")
            issues = []
            for k, v in stk_res.items():
                self.__check_reqs(requests_sent)
                bs = await self.__get_balance_sheet(session, k)
                requests_sent += 1
                try:
                    net_debt = int(bs[0]["netDebt"])
                    if net_debt > 0:
                        issues.append(k)
                        continue
                    current_assets = int(bs[0]["totalCurrentAssets"])
                    total_liabilities = int(bs[0]["totalLiabilities"])
                    ncav = current_assets - total_liabilities
                    if ncav < 0:
                        issues.append(k)
                        continue
                    v['NCAV'] = ncav
                    v['NCAV Ratio'] = round(v['Market Cap']/ncav, 1)
                except:
                    issues.append(k)
                    continue
            
            for i in issues:
                stk_res.pop(i)
            print(f"Phase III complete.\n{len(issues)} stocks removed")

            issues = []
            for k, v in stk_res.items():
                hist = await self.__get_historical(session, k)
                requests_sent += 1 
                self.__check_reqs(requests_sent)
                try:
                    five_year_max = round(max([i['close'] for i in hist['historical']]), 2)
                    five_year_price_metric = ((five_year_max - hist['historical'][0]['close'])/hist['historical'][0]['close']) * 100
                    v['5Y Price Metric'] = round(five_year_price_metric,2)
                    v['Current Price'] = round(hist['historical'][0]['close'], 2)
                    v['5Y Max'] = five_year_max
                except:
                    issues.append(k)
                    continue
            
            for i in issues:
                stk_res.pop(i)
            print(f"Phase IV complete.\n{len(issues)} stocks removed")

        print(f"{requests_sent} requests sent")
        return stk_res