from stock_info import StockInfo
import json

class Screener:
    def __init__(self) -> None:
        self.previously_seen_stocks = list() # call to db
        self.newly_added = list()
        self.all_tickers = self.__populate_tickers_arr()

    def is_positive_ncav(self)->bool:
        return self.calculate_ncav() > 0

    def calculate_ncav(self) -> float:
        pass

    def is_postitive_net_debt(self)->bool:
        pass

    def calculate_total_dividends(self) -> float:
        pass

    def calculate_total_buybacks(self) -> float:
        pass

    def calculate_payback_rating(self, average_earnings:float, dividends:float, buyback_value: float, )->float:
        # if  we took all the cash & equivalents plus the average 5Y earnings and added them together, how long would it take to pay back the current market cap.
        pass

    def calculate_average_earnings(self, time_frame: int) -> float:
        pass
    
    def run(self) -> None:
        for stock in self.all_tickers:
            # call InteractiveBrokers API to get remaining financial data.
            ncav = self.calculate_ncav()
            if ncav > 0:
                average_earnings = self.calculate_average_earnings(time_frame=5)
                dividends = self.calculate_total_dividends()
                buyback_value = self.calculate_total_buybacks()
                payback_rating = self.calculate_payback_rating(average_earnings, dividends, buyback_value)
                if payback_rating <= 3 and stock not in self.previously_seen_stocks:
                    self.__update_db(stock)
                    self.newly_added.append(stock)
        
        self.__populate_csv()
        print(f"Screener complete. {len(self.newly_added)} new stocks added to the Google Sheet.")
                

    def __populate_tickers_arr(self, path:str = "tickers.json") -> list[str]:
        with open(path, 'r') as json_file:
            data_arr = json.load(json_file)
        return data_arr
        
    
    def __update_db(self) -> None:
        pass

    def __populate_csv(self) -> None:
        pass



