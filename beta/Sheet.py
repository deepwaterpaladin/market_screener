################
# Sheet Schema #
################
# Ticker: str | Name: str | Payback Rating: float | NCAV Ratio: float | Average Yield: str(float)% | HQ Country | Exchange Country
# 
# Sheet Name: Date

class Sheet:
    def __init__(self, key:str) -> None:
        self.key = key
        self.url = ""
    
    def add_row_data(self, data: dict) -> None:
        return NotImplementedError
    
    def sort_values(self) -> None:
        return NotImplementedError
    
    def get_previously_seen_tickers(self) -> list[str]:
        return NotImplementedError