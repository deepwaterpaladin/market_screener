from datetime import datetime
import gspread
from time import sleep
import re

class Sheet:
    def __init__(self, sheet_path:str = "./service_account.json", file_name:str = 'Screener') -> None:
        self.service_account = gspread.service_account(filename = sheet_path)
        self.file = self.service_account.open(file_name)
        self.today = datetime.now()
        self._was_sheet_added_today = False
        self.month_dict = {
                            1: "Jan",
                            2: "Feb",
                            3: "Mar",
                            4: "Apr",
                            5: "May",
                            6: "Jun",
                            7: "Jul",
                            8: "Aug",
                            9: "Sep",
                            10: "Oct",
                            11: "Nov",
                            12: "Dec"}

    def __get_worksheet_names(self) -> list[gspread.Worksheet]:
        try:
            return self.file.worksheets()
        except:
            return []
    
    def __extract_date_from_string(self, input_str):
        pattern = r"'([^']+)'"
        match = re.search(pattern, input_str)
        if match:
            date_str = match.group(1)
            return date_str
        return None
    
    def __add_header(self) -> None:
        sheet = self.__get_worksheet_names()[-1]
        sheet.append_row(values= ["Ticker", "Company Name", "NCAV Ratio", "Payback Rating", "Average Yield", "HQ Country", "Exchange Country"],table_range='A1:G1')

    def __add_header_v2(self) -> None:
        sheet = self.__get_worksheet_names()[-1]
        sheet.append_row(values= ["Ticker", "Company Name", "NCAV Ratio",  "EV/aFCF", "P/TBV Ratio", "Enterprise Value", "P/aFCF Ratio", "Country"],table_range='A1:G1')
    
    def add_row_data(self, data: dict) -> None:
        sheet = self.__get_worksheet_names()[-1]
        itr = 2
        for k, v in data.items():
            payload = [k, str(v['Name']), v["NCAV Ratio"], v["Payback Rating"], v["5Y average"], str(v['HQ Location']), v["Exchange Location"]]
            sheet.append_row(values= payload, table_range=f'A{itr}:G{itr}')
            itr+=1

        print("data added to spreadsheet.")
    
    def add_row_data_v2(self, data: dict) -> None:
        sheet = self.__get_worksheet_names()[-1]
        itr = 2
        for k, v in data.items():
            payload = [k, str(v['Name']), v["NCAV Ratio"], v["EV/aFCF"], v["P/TBV Ratio"], v["EV"], v["P/aFCF Ratio"],str(v['Country'])]
            sheet.append_row(values= payload, table_range=f'A{itr}:G{itr}')
            itr+=1
            if itr % 60 == 0:
                print("Waiting 120 seconds to avoid exceeding API limit.")
                sleep(120)

        print(f"{itr-2} companies added to spreadsheet.")
    
    def get_all_worksheets(self) -> list[gspread.Worksheet]:
        try:
            return self.__get_worksheet_names()
        except:
            return []
    
    def create_new_tab(self) -> None:
        try:
            name = f"{self.today.day}-{self.month_dict[self.today.month]}-{self.today.year}"
            self.file.add_worksheet(title = name, rows = 0, cols = 0)
            self.__add_header()
            print(f"Sheet {name} added.")
            self._was_sheet_added_today = True
        except:
            print("Unable to add new tab. Tab already exists.")
    
    def create_new_tab_v2(self) -> None:
        try:
            name = f"{self.today.day}-{self.month_dict[self.today.month]}-{self.today.year}"
            self.file.add_worksheet(title = name, rows = 0, cols = 0)
            self.__add_header_v2()
            print(f"Sheet {name} added.")
            self._was_sheet_added_today = True
        except:
            print("Unable to add new tab. Tab already exists.")    
    
    def get_previously_seen_tickers(self)-> list[str]:
        try:
            today = f"{self.today.day}-{self.month_dict[self.today.month]}-{self.today.year}"
            if today == self.__extract_date_from_string(str(self.__get_worksheet_names()[-1])):
                most_recent_sheet = self.__extract_date_from_string(str(self.__get_worksheet_names()[-2]))
            else:
                most_recent_sheet = self.__extract_date_from_string(str(self.__get_worksheet_names()[-1]))
            return [item for sublist in self.file.values_get(f"{most_recent_sheet}!A2:A100")['values'] for item in sublist]
        except:
            return []
    
    def get_all_previously_seen_tickers(self) -> list[str]:
        '''
        Returns all tickers seen in the last year (52 weeks).
        '''
        seen = []
        sheets = []
        all_sheets = self.get_all_worksheets()
        weeks = len(all_sheets)
        if weeks > 52:
            sheets = all_sheets[-52:]
        else:
            sheets = all_sheets
        
        for sheet in sheets:
            seen.append(sheet.get_values("A2:A1000"))
        
        return [i[0] for sub in seen for i in sub if i]
