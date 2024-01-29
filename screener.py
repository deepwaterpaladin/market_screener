from stock_info import StockInfo
import json

class Screener:
    def __init__(self) -> None:
        self.previously_seen_stocks = list() # call to db
        self.newly_added = dict()
        self.all_tickers = self.__populate_tickers_arr()

    def is_positive_ncav(self)->bool:
        return self.calculate_ncav() > 0

    def calculate_ncav(self, current_assets: float, total_liabilities: float, preferred_stock: float = 0.0) -> float:
        """
        Calculate Net Current Asset Value (NCAV).

        Parameters:
        - current_assets (float): Total current assets.
        - total_liabilities (float): Total liabilities.

        Returns:
        - float: NCAV (Net Current Asset Value).
        """
        # ncav = current_assets - (total_liabilities + preferred_stock)
        ncav = sum([current_assets, total_liabilities, preferred_stock])
        return ncav

    def calculate_net_debt(self, total_debt: float, cash_and_equivalents: float) -> float:
        return total_debt - cash_and_equivalents

    def calculate_total_dividends(self, frequency:str, dividend:float, free_float: int) -> float:
        pass

    def calculate_total_buybacks(self) -> float:
        pass

    def calculate_payback_rating(self, average_earnings:float, dividends:float, buyback_value: float, )->float:
        # if  we took all the cash & equivalents plus the average 5Y earnings and added them together, how long would it take to pay back the current market cap.
        pass

    def calculate_average_earnings_yield(self, fcff_values, market_cap_values, threshold_percentage=10):
        """
        Calculate the average 5-year annual Free Cash Flow yield.

        Parameters:
        - fcff_values (list): List of Free Cash Flow values over 5 years.
        - market_cap_values (list): List of Market Capitalization values over 5 years.
        - threshold_percentage (float): Threshold for FCF yield (default is 10%).

        Returns:
        - float: Average 5-year annual FCF yield.
        """
        # Calculate FCF yields for each year
        fcff_yields = [fcf / market_cap * 100 for fcf, market_cap in zip(fcff_values, market_cap_values)]
        # Filter FCF yields that meet the threshold
        qualified_fcff_yields = [yield_value for yield_value in fcff_yields if yield_value >= threshold_percentage]
        print(f"Yields >=10% {qualified_fcff_yields}")
        # Calculate the average of qualified FCF yields
        if qualified_fcff_yields:
            average_5y_fcff_yield = sum(qualified_fcff_yields) // len(qualified_fcff_yields)
            return average_5y_fcff_yield
        else:
            return 0  # Return 0 if there are no qualified FCF yields
    
    def calculate_ttm_free_cash_flow(self, fcff_values:list[float]): # most likely will be dataframe
        """
        Calculate Trailing Twelve Months (TTM) Free Cash Flow.

        Parameters:
        - fcff_values (list): List of Free Cash Flow values for each month.

        Returns:
        - float: TTM Free Cash Flow.
        """
        if len(fcff_values) >= 12:
            ttm_free_cash_flow = sum(fcff_values[-12:])
            return ttm_free_cash_flow
        elif len (fcff_values) == 1:
            return fcff_values[0]
        else:
            return 0

    
    def execute(self, ticker:str, market_caps: list[float], current_assets: float, total_liabilities: float, free_cash_flows: list[float], total_debt: float, cash_and_equivalents: float, dividends_arr:list[float] | None = None) -> None:
        current_market_cap = market_caps[-1]
        is_market_cap_below_ncav = current_market_cap <= self.calculate_ncav(current_assets = current_assets, total_liabilities = total_liabilities)
        is_fcf_yield_greater_than_10 = self.calculate_average_earnings_yield(fcff_values = free_cash_flows, market_cap_values = market_caps) >= 10
        is_positive_ttm = free_cash_flows[-1] > 0
        net_debt = self.calculate_net_debt(total_debt, cash_and_equivalents)
        has_dividends = type(dividends_arr) != None
        if is_market_cap_below_ncav and is_fcf_yield_greater_than_10 and is_positive_ttm and net_debt <= 0 and has_dividends:
            # check if ticker is in self.previously_seen_stocks
            self.newly_added[ticker] = {"Market Cap at or below NCAV": is_market_cap_below_ncav, "Average 5Y annual Free Cash Flow yield at 10%": is_fcf_yield_greater_than_10, "TTM is Positive": is_positive_ttm, "Net-Debt": net_debt, "Has paid dividends or buybacks": has_dividends}

    
    def run(self) -> None:
        for stock in self.all_tickers:
            # call InteractiveBrokers API to get remaining financial data.
            data_arr = [100, 40] # replace with call to data API
            ncav = self.calculate_ncav(data_arr[0], data_arr[1])
            if ncav > 0:
                average_earnings = self.calculate_average_earnings_yield(time_frame=5)
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



