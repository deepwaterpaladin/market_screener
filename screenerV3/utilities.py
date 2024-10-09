import aiohttp
from dotenv import load_dotenv
import os
import json
from screener.Sheet import Sheet

load_dotenv()

class Handler:
    def __init__(self) -> None:
        self.api_key = os.environ['FMP_KEY']
    
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
    
    def process_tickers(self, sheet_client:Sheet, path: str = None) -> dict[str:list]:
        """
        Processes tickers from a JSON file.

        Parameters:
        - `path` (str): The path to the JSON file containing stock tickers. Defaults to None.
        - `tickers` (dict): A dictionary of tickers. Defaults to None.

        Returns:
        - `dict`: A dictionary containing processed tickers.
        """
        t = self.__read_json_file(path)
        ret = {}
        previously_seen = sheet_client.get_all_previously_seen_tickers()
        removed = 0
        for k, v in t.items():
            init = len(v)
            ret[k]=[i for i in v if i not in previously_seen]
            removed += init-len(ret[k])
        
        print(f"{removed} tickers removed for being screened within the passed year.")
        return ret
    
    async def get_profile(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key}') as response:
            try:
                return await response.json()
            except Exception as e:
                pass
    
    async def get_historical(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={self.key}') as response:
            try:
                return await response.json()# if response.status == 200 else print("Hit API limit. Waiting 55 seconds.") and sleep(55)
            except Exception as e:
                pass
    
    async def get_balance_sheet(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period=quarter&limit=5&apikey={self.key}') as response:
            try:
                return await response.json()# if response.status == 200 else print("Hit API limit. Waiting 55 seconds.") and sleep(55)
            except Exception as e:
                pass
    
    async def get_cashflow(self, session: aiohttp.ClientSession, ticker: str) -> str:
        async with session.get(f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit=5&apikey={self.key}') as response:
            try:
                return await response.json()# if response.status == 200 else print("Hit API limit. Waiting 55 seconds.") and sleep(55)
            except Exception as e:
                pass

    async def get_key_metrics(self, session: aiohttp.ClientSession, ticker: str) -> str:
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
    