################
# Sheet Schema #
################
# Ticker: str | Name: str | Payback Rating: float | NCAV Ratio: float | Average Yield: str(float)% | HQ Country | Exchange Country
# 
# Sheet Name: Date

import gspread
from datetime import datetime
import re

class Sheet:
    def __init__(self) -> None:
        self.service_account = gspread.service_account(filename="./service_account.json")
        self.file = self.service_account.open("screener")
        self.today = datetime.now()

    def __get_worksheet_names(self) -> list[gspread.Worksheet]:
        return self.file.worksheets()
    
    def __extract_date_from_string(self, input_str):
        pattern = r"'([^']+)'"
        match = re.search(pattern, input_str)
        if match:
            date_str = match.group(1)
            return date_str
        return None
    
    def __add_header(self) -> None:
        sheet = self.__get_worksheet_names()[-1]
        sheet.append_row(values= ["Ticker", "Company Name", "Payback Rating", "NCAV Ratio", "Average Yield", "HQ Country", "Exchange Country"],table_range='A1:G1')

    def add_row_data(self, data: dict) -> None:
        sheet = self.__get_worksheet_names()[-1]
        itr = 2
        for k, v in data.items():
            payload = [k, str(v['Name']), "tbd", "tbd", "tbd", str(v['HQ Location']), "tbd"] # TODO: fix this
            sheet.append_row(values= payload, table_range=f'A{itr}:G{itr}')
            itr+=1
        print("data added to spreadsheet.")
    
    def sort_values(self) -> None:
        pass
    
    def get_all_worksheets(self) -> list[gspread.Worksheet]:
        return self.__get_worksheet_names()
    
    def create_new_tab(self) -> None:
        try:
            name = f"{self.today.month}-{self.today.day}-{self.today.year}"
            self.file.add_worksheet(title = name, rows = 0, cols = 0)
            self.__add_header()
            print(f"Sheet {name} added.")
        except:
            print("Unable to add new tab. Tab already exists.")
    
    def get_previously_seen_tickers(self)-> list[str]:
        today = f"{self.today.month}-{self.today.day}-{self.today.year}"
        if today == self.__extract_date_from_string(str(self.__get_worksheet_names()[-1])):
            most_recent_sheet = self.__extract_date_from_string(str(self.__get_worksheet_names()[-2]))
        else:
            most_recent_sheet = self.__extract_date_from_string(str(self.__get_worksheet_names()[-1]))
        return [item for sublist in self.file.values_get(f"{most_recent_sheet}!A2:A100")['values'] for item in sublist]