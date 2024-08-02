from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from .Sheet import Sheet
from .Utilities import Utilities
import pandas as pd
import aiohttp
import asyncio
import os
import json

load_dotenv()

class AsyncScreener2:
    def __init__(self, ticker_path: str) -> None:
        self.tickers = Utilities.procress_tickers(ticker_path)
        self.key = os.environ['FMP_KEY']
        self.results = {}
    

    async def __handle_screener(self, tickers: list[str], debug: bool = False):
        if debug:
            print(f"{len(self.tickers)//2}/{len(len(self.tickers))} tickers processed...")
        async with aiohttp.ClientSession() as session:
            pass
    
    async def run_async(self, batch_size:int=100):
        tickers_arr = [i for sublist in self.tickers.values() for i in sublist]
        for i in range(0, len(tickers_arr), batch_size):
            is_middle = i == len(tickers_arr)//2
            start = datetime.now()
            await self.__handle_tickers(tickers=tickers_arr[i:i+batch_size], debug=is_middle)
            sleep(61-(datetime.now()-start).seconds)
        print(f"{len(self.results)} stocks remaining after screening")