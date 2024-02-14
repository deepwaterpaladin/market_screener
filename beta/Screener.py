from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from Sheet import Sheet
from threading import Thread
import yfinance as yf
from time import sleep
import os
import requests
import json

load_dotenv()
pd.set_option('display.float_format', lambda x: '%.3f' % x)

class Screener:
    """
    The `Screener` class is designed to screen and analyze stocks based on various criteria such as dividends, market cap,
    net debt, and five-year average yield. It leverages Yahoo Finance (yfinance), Financial Modeling Prep (FMP) API, and Google Sheets.
    """
    
    def __init__(self, path: str= None) -> None:
        self.tickers = self.__process_tickers(path)
        self.key = os.environ['CLIENT_FMP_KEY']
        self.sorted = bool
        self.results = dict()
        self.sheet_client = Sheet()
        self.previous = self.sheet_client.get_previously_seen_tickers()
    
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
    
    def __process_tickers(self, path: str= None, tickers: dict[str:list] = None) -> dict[str:list]:
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
        # for k, v in t.items():
        #     t[k] = [i.split(':')[1]+clean[k] for i in t[k]]
        
        return t
    
    def __has_dividends_or_buybacks(self, ticker: yf.Ticker) -> bool:
        """
        Checks if a stock has dividends or buybacks.

        Parameters:
        - `ticker` (yf.Ticker): The Ticker object for the stock.

        Returns:
        - `bool`: True if the stock has dividends or buybacks, False otherwise.
        """
        has_dividends = ticker.dividends.sum() > 0
        if has_dividends:
            return True
        try:
            has_buybacks = ticker.quarterly_cashflow.loc['Repurchase Of Capital Stock'].sum() < 0
            return has_buybacks
        except:
            return False
        
    def __get_cashflow(self, ticker: str, span:int = 5) -> float:
        url = f'https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period=annual&limit={span}&apikey={self.key}'
        response = requests.get(url)
        if response.status_code > 399:
            print(f"API returned response code: {response.status_code}")
        return response.json()

    def __get_profile(self, ticker: str) -> str:
        """
        Retrieves profile information for a given stock.

        Parameters:
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `str`: The profile information for the stock.
        """
        url = f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.key}'
        response = requests.get(url)
        if response.status_code > 399:
            print(f"API returned response code: {response.status_code}")
        return response.json()
    
    def __get_balance_sheet(self, ticker:str) -> str:
        """
        Retrieves profile information for a given stock.

        Parameters:
        - `ticker` (str): The stock ticker symbol.

        Returns:
        - `str`: The profile information for the stock.
        """
        url = f'https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?apikey={self.key}'
        response = requests.get(url)
        if response.status_code > 399:
            print(f"API returned response code: {response.status_code}")
        return response.json()
    
    def __screen_dividends_and_buybacks(self, ret_dict:dict[str:dict], rs:list=[], debug:bool = False) -> list[str]:   
        ctn = 0
        m = []
        for k, v in ret_dict.items():
            try:
                ctn +=1
                t = yf.Ticker(k)
                has_dividends_or_buybacks = self.__has_dividends_or_buybacks(t)
                if has_dividends_or_buybacks:
                    v["Has Dividends or Buybacks"] = True
                else:
                    m.append(k)
            except:
                m.append(k)

            # TODO: Remove b4 shipping
            percentage_completed = (ctn + 1) / len(ret_dict) * 100
            if percentage_completed % 5 == 0 and debug:
                print(f"Processing: {percentage_completed:.0f}% complete")
        rs.append(ret_dict)
        return m
       
    def __screen_ncav(self, ret_dict:dict[str:dict], debug:bool = False) -> list[str]:
        """
        Screens stocks based on Market Cap <= NCAV (Net Current Asset Value).

        Parameters:
        - `ret_dict` (dict): A dictionary containing stock information to be screened.
        - `debug` (bool): If True, prints debug information. Defaults to False.

        Returns:
        - `list[str]`: A list of tickers that did not meet the screening criteria.
        """
        ctn = 0
        m = []
        for k, v in ret_dict.items():
            try:
                ctn +=1
                t = yf.Ticker(k)
                qbs = t.quarterly_balance_sheet
                total_liabilities = qbs.loc['Total Liabilities Net Minority Interest'][0]
                current_assets = qbs.loc['Current Assets'][0]
                market_cap = t.info['marketCap']
                ncav = current_assets - total_liabilities
                #is_market_cap_less_or_equal_to_ncav = market_cap <= ncav #self.__has_market_cap_less_than_ncav(t)
                if ncav > 0:
                    v["Positive NCAV"] = True
                    v["Market Capitalization"] = int(market_cap)
                    v["NCAV Ratio"] = round(market_cap / ncav, 1)
                else:
                    m.append(k)
            except:
                m.append(k)

            # TODO: Remove b4 shipping
            percentage_completed = (ctn + 1) / len(ret_dict) * 100
            if percentage_completed % 5 == 0 and debug:
                print(f"Processing: {percentage_completed:.0f}% complete")
        
        return m

    def __screen_net_debt(self, ret_dict:dict[str:dict]) -> list[str]:
        """
        Screens stocks based on Net Debt.

        Parameters:
        - `ret_dict` (dict): A dictionary containing stock information to be screened.

        Returns:
        - `list[str]`: A list of tickers that did not meet the screening criteria.
        """
        m = []
        for k, v in ret_dict.items(): # check "Net Debt".
            try:
                ticker = yf.Ticker(k)
                net_debt = ticker.quarterly_balance_sheet.loc['Net Debt'][0]
                has_net_debt = net_debt <= 0
                if has_net_debt:
                    v["Net Debt"] = net_debt
                else:
                    m.append(k)
            except:
                try:
                    net_debt = ticker.quarterly_balance_sheet.loc["Total Debt"][0]
                    has_net_debt = net_debt > 0 
                    if has_net_debt:
                        v["Net Debt"] = net_debt
                    else:
                        m.append(k)
                except:
                    m.append(k)
        
        return m

    def __screen_five_year_yield(self, ret_dict:dict[str:dict]) -> float:
        """
        Screens stocks based on five-year average yield.

        Parameters:
        - `ret_dict` (dict): A dictionary containing stock information to be screened.

        Returns:
        - `list[str]`: A list of tickers that did not meet the screening criteria.
        """
        m = []
        print(f"{len(ret_dict)} stocks to be screened at `__screen_five_year_yield`")
        for k, v in ret_dict.items():
            try:
                profile = self.__get_profile(k)[0]
                mkt_cap = int(profile['mktCap'])
                v["Name"] = str(profile['companyName'])
                v["HQ Location"] = str(profile['country'])
                if v["HQ Location"] == "CN":
                    m.append(k)
                cashflow = self.__get_cashflow(k)
                five_year_fcf_average = sum([i['freeCashFlow'] for i in cashflow])/5
                v["5Y average"] = five_year_fcf_average
                val = round((five_year_fcf_average/mkt_cap)*100, 2)
                v['5Y average yield > 10%'] = val
                v["Cash & Equivalents"] = cashflow[0]["cashAtEndOfPeriod"]
                if val < 10:
                    m.append(k)
            except:
                m.append(k)
        
        return m 

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
    
    def __split_dict(self, input_dict: dict, num_slices: int) -> list[dict]:
        """
        Splits a dictionary into a specified number of slices.

        Parameters:
        - `input_dict` (dict): The dictionary to be split.
        - `num_slices` (int): The number of slices.

        Returns:
        - `list[dict]`: A list of dictionaries, each representing a slice. Used by `__handle_threads`.
        """
        dict_items = list(input_dict.items())
        slice_size = len(dict_items) // num_slices
        remainder = len(dict_items) % num_slices

        slices = []
        start = 0

        for i in range(num_slices):
            slice_end = start + slice_size + (1 if i < remainder else 0)
            slices.append(dict(dict_items[start:slice_end]))
            start = slice_end

        return slices

    def __split_list(self, arr:list[str], n:int) ->list[list[str]]:
        elements_per_sublist = len(arr) // n
        sublists = []
        for i in range(0, len(arr), elements_per_sublist):
            sublist = arr[i:i + elements_per_sublist]
            sublists.append(sublist)

        return sublists
    
    def __calculate_packback_rating(self) -> None:
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
                v["Payback Rating"] = -1 # remove

    def __sort_results_dict(self)->None:
        """
        Sort the results dictionary in place first by "NCAV Ratio" (lowest to highest)
        and then by "Payback Rating" (lowest to highest).
        """
        self.results = dict(sorted(self.results.items(), key=lambda x: (x[1]["NCAV Ratio"], x[1]["Payback Rating"])))

    def __handle_threads(self, ret_dict: dict[str:list], start_time:datetime, debug:bool = False):
        """
        Handles threaded execution of screening steps.

        Parameters:
        - `ret_dict` (dict): A dictionary containing stock information to be screened.
        - `start_time` (datetime): The start time of the screening process.
        - `debug` (bool): If True, prints debug information. Defaults to False.

        Returns:
        - `None`
        """
        steps = ['check "Has Dividends or Buybacks"', 'check "Positive NCAV"', 'check "Net Debt"', 'check "5Y average yield > 10%"','check "whitelist country"']
        removal_matrix = [[] for i in steps]

        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[0]}.")
        removal_matrix[0] = self.__screen_dividends_and_buybacks(ret_dict, debug=debug)
        print(f"Time to check dividends: {datetime.now() - start_time}")
        for i in removal_matrix[0]:
            ret_dict.pop(i)
    
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[1]}.")
        start_market_cap = datetime.now()
        removal_matrix[1] = self.__screen_ncav(ret_dict, debug=debug)
        print(f"Time to check Market Cap <= NCAV: {datetime.now() - start_market_cap}")
        for i in removal_matrix[1]:
            ret_dict.pop(i)
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[2]}.")
        start_net_debt = datetime.now()
        removal_matrix[2] = self.__screen_net_debt(ret_dict)
        print(f"Time to check Net Debt: {datetime.now() - start_net_debt}")
        for i in removal_matrix[2]:
            ret_dict.pop(i)
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[3]}.")
        start_fcf_time = datetime.now()
        removal_matrix[3] = self.__screen_five_year_yield(ret_dict)
        print(f"Time to check '5Y average yield > 10%': {datetime.now() - start_fcf_time}")
        for i in removal_matrix[3]:
            try:
                ret_dict.pop(i)
            except:
                continue
        
        self.results.update(ret_dict)
    
    def __convert_countries(self) -> None:
        """
        Converts stock tickers to their corresponding exchange locations and updates the 'Exchange Location' field in the results.
        This method iterates over the stock tickers in the results and updates the 'Exchange Location' field based on the last part of the ticker.
        """
        exchange_dict = {
            "PA":"France",
            "TO":"Canada",
            "T":"Japan",
            "L":"United Kingdom",
            "VI":"Austria",
            "BR":"Belgium",
            "TL":"Estonia",
            "DE":"Germany",
            "AT":"Greece",
            "BD":"Hungary",
            "MI":"Italy",
            "RG":"Latvia",
            "VS":"Lithuania",
            "AS":"Netherlands",
            "LS":"Portugal",
            "HE":"Finland",
            "MC":"Spain",
            "ST":"Sweden",
            "NZ":"New Zealand",
            "PR":"Czech Republic",
            "SW":"Switzerland"
        }
        for k, v in self.results.items():
            if '.' in k:
                split = k.split('.')
                v["Exchange Location"] = exchange_dict[split[-1]]
            else:
                v["Exchange Location"] = "United States"

    def run(self, debug: bool = False) -> None:
        start_time = datetime.now()
        ticker_arr = [item for sub in self.tickers.values() for item in sub]
        ret_dict = {i:{"Name":str, "HQ Location":str, "Has Dividends or Buybacks": bool, "Net Debt": float, "5Y average yield > 10%": bool, "Positive NCAV": bool} for i in ticker_arr}
        steps = ['check "Has Dividends or Buybacks"', 'check "Positive NCAV"', 'check "Net Debt"', 'check "5Y average yield > 10%"','check "whitelist country"']
        removal_matrix = [[] for i in steps]
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[0]}.")
        removal_matrix[0] = self.__screen_dividends_and_buybacks(ret_dict, debug=debug)
        print(f"Time to check dividends: {datetime.now() - start_time}")
        for i in removal_matrix[0]:
            ret_dict.pop(i)
    
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[1]}.")
        start_market_cap = datetime.now()
        removal_matrix[1] = self.__screen_ncav(ret_dict, debug=debug)
        print(f"Time to check Market Cap <= NCAV: {datetime.now() - start_market_cap}")
        for i in removal_matrix[1]:
            ret_dict.pop(i)
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[2]}.")
        start_net_debt = datetime.now()
        removal_matrix[2] = self.__screen_net_debt(ret_dict)
        print(f"Time to check Net Debt: {datetime.now() - start_net_debt}")
        for i in removal_matrix[2]:
            ret_dict.pop(i)
        
        if debug:
            print(f"{len(ret_dict)} Tickers to be screened for step {steps[3]}.")
        start_fcf_time = datetime.now()
        removal_matrix[3] = self.__screen_five_year_yield(ret_dict)
        print(f"Time to check '5Y average yield > 10%': {datetime.now() - start_fcf_time}")
        for i in removal_matrix[3]:
            ret_dict.pop(i)
        
        self.results = ret_dict

        print(f"Total run time {datetime.now() - start_time}")
 
    def run_fully_threaded(self, thread_sum: int = 2, debug: bool = False) -> None:
        """
        Run the screening process using multiple threads.

        Parameters:
            thread_sum (int): Number of threads to use.
                             Defaults to 2.
            debug (bool): Whether to print debug information. Defaults to False.
        """
        threads = []
        start = datetime.now()
        ticker_arr = [item for sub in self.tickers.values() for item in sub]
        ret_dict = {i:{"Name":str, "HQ Location":str, "Exchange Location":str, "Has Dividends or Buybacks": bool, "Net Debt": float, "Cash & Equivalents": float, "5Y average yield > 10%": bool, "5Y average": float, "Positive NCAV": bool, "Market Capitalization": float, "NCAV Ratio": float, "Payback Rating": float} for i in ticker_arr}
        split = self.__split_dict(ret_dict, thread_sum)
        for i in range(len(split)):
            is_last = i == len(split)-1
            thread = Thread(target= self.__handle_threads, args=[split[i], datetime.now(), is_last])
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        print(f"Calculating payback rating for {len(self.results)} Stocks.")
        self.__calculate_packback_rating()
        self.__convert_countries()
        negative_payback = []
        for k, v in self.results.items():
            if v["Payback Rating"] == -1:
                negative_payback.append(k)
        
        for i in negative_payback:
            self.results.pop(i)
        
        print(f"{len(self.results)} stocks remaining.")
        print(f"Total run time {datetime.now() - start}")
     
    def __handle_threadsV2(self, ticker_arr: list[str], start:datetime, debug:bool = False):
        res = {i:{"Name":str, "HQ Location":str, "Exchange Location":str, "Has Dividends or Buybacks": bool, "Net Debt": float, "Cash & Equivalents": float, "5Y average yield > 10%": bool, "5Y average": float, "Positive NCAV": bool, "Market Capitalization": float, "NCAV Ratio": float, "Payback Rating": float} for i in ticker_arr}
        ticker_sum = len(ticker_arr)
        garbage = []
        timer = datetime.now()
        for i in range(0, ticker_sum):
            if i == ticker_sum//2 or i == ticker_sum//4 or i == ticker_sum//8 and debug:
                print(f"Processed {i}/{ticker_sum}")
            if i % 9:
                ex_time = datetime.now() - timer
                if ex_time.seconds < 60:
                    sleep((60-ex_time.seconds)+0.5)
                timer = datetime.now()
            try:
                ticker = ticker_arr[i]
                profile = self.__get_profile(ticker)
                cashflow = self.__get_cashflow(ticker)
                balance_sheet = self.__get_balance_sheet(ticker)
                net_debt = int(balance_sheet[0]["netDebt"])
                if net_debt > 0:
                    res.pop(ticker)
                    continue
                res[ticker]["Net Debt"] = net_debt   
            except:
                garbage.append(ticker)
                continue 
            try:
                div = float(profile[0]["lastDiv"])
                if div > 0:
                    res[ticker]["Has Dividends or Buybacks"] = True
            except:
                try:
                    buyback = sum([i["commonStockRepurchased"] for i in cashflow])
                    if buyback < 0:
                        res[ticker]["Has Dividends or Buybacks"] = True
                    else:
                        garbage.append(ticker)
                        continue
                except:
                    # no buybacks or dividends
                    garbage.append(ticker)
                    continue
            
            current_assets = int(balance_sheet[0]["totalCurrentAssets"])
            total_liabilities = int(balance_sheet[0]["totalLiabilities"])
            ncav = current_assets - total_liabilities
            if ncav < 0:
                garbage.append(ticker)
                continue
            res[ticker]["Positive NCAV"] = True
            market_cap = int(profile[0]["mktCap"])
            res[ticker]["NCAV Ratio"] = round(market_cap / ncav, 1)
            five_year_fcf_average = sum([i['freeCashFlow'] for i in cashflow])/5
            res[ticker]["5Y average"] = five_year_fcf_average
            val = round((five_year_fcf_average/market_cap)*100, 2)
            if val < 10:
                garbage.append(ticker)
                continue
            res[ticker]['5Y average yield > 10%'] = val
            res[ticker]["Cash & Equivalents"] = cashflow[0]["cashAtEndOfPeriod"]
            
            res[ticker]["Market Capitalization"] = market_cap
            res[ticker]["Name"] = profile[0]["companyName"]
            res[ticker]["HQ Location"] = profile[0]["country"]
            res[ticker]["Exchange Location"] = profile[0]["exchange"]
            
        for i in garbage:
            res.pop(i)
        self.results.update(res)
        if debug:
            print(f"Screening complete. Total Execution Time: {datetime.now() - start}")
    
    def run_threadedV2(self, thread_sum: int = 4, debug:bool = False) -> None:
        ticker_arr = [item for sub in self.tickers.values() for item in sub]
        split = self.__split_list(ticker_arr, thread_sum)
        threads = [Thread(target= self.__handle_threadsV2, args=[split[i], datetime.now(), debug]) for i in range(thread_sum)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        if debug:
            print(f"Calculating payback rating for {len(self.results)} Stocks.")
        self.__calculate_packback_rating()
        

    
    def runV2(self, debug:bool = False) -> None:
        start = datetime.now()
        ticker_arr = [item for sub in self.tickers.values() for item in sub]
        res = {i:{"Name":str, "HQ Location":str, "Exchange Location":str, "Has Dividends or Buybacks": bool, "Net Debt": float, "Cash & Equivalents": float, "5Y average yield > 10%": bool, "5Y average": float, "Positive NCAV": bool, "Market Capitalization": float, "NCAV Ratio": float, "Payback Rating": float} for i in ticker_arr}
        timer = datetime.now()
        garbage = []
        for i in range(0, len(ticker_arr)):
            if i % 99:
                ex_time = datetime.now() - timer
                if ex_time.seconds < 60:
                    sleep((60-ex_time.seconds)+0.5)
                timer = datetime.now()
            ticker = ticker_arr[i]
            profile = self.__get_profile(ticker)
            cashflow = self.__get_cashflow(ticker)
            balance_sheet = self.__get_balance_sheet(ticker)
            net_debt = int(balance_sheet[0]["netDebt"])
            if net_debt > 0:
                res.pop(ticker)
                continue
            res[ticker]["Net Debt"] = net_debt       
            try:
                div = float(profile[0]["lastDiv"])
                if div > 0:
                    res[ticker]["Has Dividends or Buybacks"] = True
            except:
                try:
                    buyback = sum([i["commonStockRepurchased"] for i in cashflow])
                    if buyback < 0:
                        res[ticker]["Has Dividends or Buybacks"] = True
                    else:
                        garbage.append(ticker)
                        continue
                except:
                    # no buybacks or dividends
                    garbage.append(ticker)
                    continue
            
            current_assets = int(balance_sheet[0]["totalCurrentAssets"])
            total_liabilities = int(balance_sheet[0]["totalLiabilities"])
            ncav = current_assets - total_liabilities
            if ncav < 0:
                garbage.append(ticker)
                continue
            res[ticker]["Positive NCAV"] = True
            market_cap = int(profile[0]["mktCap"])
            res[ticker]["NCAV Ratio"] = round(market_cap / ncav, 1)
            five_year_fcf_average = sum([i['freeCashFlow'] for i in cashflow])/5
            res[ticker]["5Y average"] = five_year_fcf_average
            val = round((five_year_fcf_average/market_cap)*100, 2)
            if val < 10:
                garbage.append(ticker)
                continue
            res[ticker]['5Y average yield > 10%'] = val
            res[ticker]["Cash & Equivalents"] = cashflow[0]["cashAtEndOfPeriod"]
            
            res[ticker]["Market Capitalization"] = market_cap
            res[ticker]["Name"] = profile[0]["companyName"]
            res[ticker]["HQ Location"] = profile[0]["country"]
            res[ticker]["Exchange Location"] = profile[0]["exchange"]
            
        # self.results = res
        for i in garbage:
            res.pop(i)
        
        self.results.update(res)
        self.__calculate_packback_rating()
        if debug:
            print(f"Screening complete. Total Execution Time: {datetime.now() - start}")

        
    
    def create_xlsx(self, file_path:str) -> None:
        """
        Creates an Excel file with the screening results.

        Parameters:
        - `file_path` (str): The path to the Excel file.

        Returns:
        - `None`
        """
        self.__sort_results_dict()
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
        self.__sort_results_dict()
        cleaned = len(self.results)
        if debug:
            print(f"{starting_size - cleaned} tickers removed (previously present in google sheet).")
        
        self.sheet_client.add_row_data(self.results)
        
        if debug:
            print("Google Sheet updated.")
   