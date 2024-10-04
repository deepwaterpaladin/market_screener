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