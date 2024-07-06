from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from screener.Sheet import Sheet
import pandas as pd
import aiohttp
import asyncio
import os
import json

load_dotenv()

class AsyncScreener:
    def __init__(self, ticker_path: str, sheet_path:str = "./service_account.json", sheet_name: str = "Screener"):
        self.tickers = self.__process_tickers(ticker_path)
        self.key = os.environ['FMP_KEY']
        self.sheet_client = Sheet(sheet_path= sheet_path, file_name=sheet_name)
        self.results = {}
        self.negative_paypack_rating = []
        self.previous = self.sheet_client.get_all_previously_seen_tickers()

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

    def __sort_results_dict(self) -> None:
        """
        Sort the results dictionary in place first by "NCAV Ratio" (lowest to highest)
        and then by "Payback Rating" (lowest to highest).
        """
        self.results = dict(sorted(self.results.items(), key=lambda x: (x[1]["NCAV Ratio"], x[1]["Payback Rating"])))
    
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
    
    def __calculate_packback_rating(self, debug: bool = False) -> None:
        """
        Calculates the payback rating for the screening results.

        Returns:
        - `None`
        """
        for k, v in self.results.items():
            cash_equivalents = v.get("Cash & Equivalents", 0)
            earnings_average = v.get("5Y average", 0)
            market_cap = v.get("Market Capitalization", 0)
            if cash_equivalents > market_cap:
                v["Payback Rating"] = 0.5
            elif market_cap <= (cash_equivalents + earnings_average):
                v["Payback Rating"] = 1
            elif market_cap <= (cash_equivalents + (earnings_average * 2)):
                v["Payback Rating"] = 2
            elif market_cap <= (cash_equivalents + (earnings_average * 3)):
                v["Payback Rating"] = 3
            else:
                self.negative_paypack_rating.append(k)

        for i in self.negative_paypack_rating:
            self.results.pop(i)

        self.__sort_results_dict()
        if debug:
            print(
                f"Removed {len(self.negative_paypack_rating)} with a negative payback rating.")

    async def __get_data(self, session: aiohttp.ClientSession, ticker: str) -> tuple:
        profile = await self.__get_profile(session, ticker)
        cashflow = await self.__get_cashflow(session, ticker)
        balance_sheet = await self.__get_balance_sheet(session, ticker)
        return profile, cashflow, balance_sheet

    async def __get_profile(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key}') as response:
            return await response.json()

    async def __get_cashflow(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=5&apikey={self.key}') as response:
            return await response.json()

    async def __get_balance_sheet(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}') as response:
            return await response.json()
    
    async def get_all_shares_float(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://financialmodelingprep.com/api/v4/shares_float/all?apikey={self.key}') as response:
                return await response.json()

    async def __handle_tickers(self, tickers: list[str], debug: bool = False) -> None:
        if debug:
            print(
                f"{len(self.tickers)//2}/{len(len(self.tickers))} tickers processed...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.__get_data(session, ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks)
            for ticker, (profile, cashflow, balance_sheet) in zip(tickers, results):
                try:
                    net_debt = int(balance_sheet[0]["netDebt"])
                    if net_debt > 0:
                        continue
                except:
                    continue
                try:
                    div = float(profile[0]["lastDiv"])
                    if div > 0:
                        has_dividends = True
                    else:
                        buyback = sum([i["commonStockRepurchased"]
                                      for i in cashflow])
                        if buyback < 0:
                            has_dividends = True
                        else:
                            continue
                except:
                    try:
                        buyback = sum([i["commonStockRepurchased"]
                                      for i in cashflow])
                        if buyback < 0:
                            has_dividends = True
                        else:
                            continue
                    except:
                        continue
                try:
                    current_assets = int(balance_sheet[0]["totalCurrentAssets"])
                    total_liabilities = int(balance_sheet[0]["totalLiabilities"])
                    ncav = current_assets - total_liabilities
                    if ncav < 0:
                        continue
                    market_cap = int(profile[0]["mktCap"])
                    if market_cap <= 0:
                        continue
                    five_year_fcf_average = sum(
                        [i['freeCashFlow'] for i in cashflow])/5
                    average_yield = round(
                        (five_year_fcf_average/market_cap)*100, 2)
                    if average_yield < 10:
                        continue
                    ratio = round(market_cap / ncav, 1)
                    country = profile[0]["country"]
                    industry = profile[0]["industry"]
                    if country == "CN" or country == "HK":
                        continue
                    if industry[:5] == "Banks" or industry[:9] == "Insurance" or industry[:10] == "Investment" or industry == "Asset Management":
                        continue
                except:
                    continue
                
                self.results[ticker] = {
                    "Name": profile[0]["companyName"],
                    "HQ Location": country,
                    "Exchange Location": profile[0]["exchange"],
                    "Industry": industry,
                    "Has Dividends or Buybacks": has_dividends,
                    "Net Debt": net_debt,
                    "Cash & Equivalents": cashflow[0]["cashAtEndOfPeriod"],
                    "5Y average yield > 10%": average_yield,
                    "5Y average": five_year_fcf_average,
                    "Positive NCAV": True,
                    "Market Capitalization": market_cap,
                    "NCAV Ratio": ratio,
                }

    async def run_async(self, batch_size=100) -> None:
        ticker_arr = [item for sublist in self.tickers.values()
                      for item in sublist]
        for i in range(0, len(ticker_arr), batch_size):
            is_middle = i == len(ticker_arr)//2
            start = datetime.now()
            await self.__handle_tickers(tickers=ticker_arr[i:i+batch_size], debug=is_middle)
            sleep(60-(datetime.now()-start).seconds)

        self.__calculate_packback_rating()
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
            print(f'ERROR: results dictionary is empty. Execute `Screener.run()` to screen the stocks. If you are still seeing this after running `Screener.run()`, there are no new stocks from the previous execution.')
        else:
            df = pd.DataFrame.from_dict(self.results, orient='index')
            df.to_excel(file_path)
            print(f"File saved to {file_path}")
    
    def update_google_sheet(self, debug:bool = False) -> None:
        """
        Method to create an Excel file with the screening results.

        Parameters:
        - `file_path` (str): The path to the Excel file.

        Returns:
        - `None`
        """
        self.sheet_client.create_new_tab()
        starting_size = len(self.results)
        self.__remove_previously_seen()
        cleaned = len(self.results)
        if debug:
            print(f"{starting_size - cleaned} tickers removed (previously present in google sheet).")
        
        self.sheet_client.add_row_data(self.results)
        
        if debug:
            print("Google Sheet updated.")
   