from dotenv import load_dotenv
from screener.Sheet import Sheet
import pandas as pd
import aiohttp
import os
import json

load_dotenv()


class BetaModule:
    def __init__(self, ticker_path: str, sheet_path:str = "./service_account.json", sheet_name: str = "Screener") -> None:
        self.sheet_client = Sheet(sheet_path= sheet_path, file_name=sheet_name)
        self.tickers = self.__process_tickers(ticker_path)
        self.key = os.environ['FMP_KEY']
        self.results = {}