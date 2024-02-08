# market_screener

## Project Requirements (High Level)

1. Market Cap at or below Net-Current-Asset-Value
1. Average 5Y annual Free Cash Flow > 10%
1. Positive TTM Free-cashflow
1. Zero or negative net-debt
1. Some 5Y dividends or buybacks present
1. Only companies from selected country HQs or exchanges
1. Run weekly; saving results to a .xlsx db

## Usage - beta

1. create `.env` file & save `FMP_KEY_1 = ****YOUR API KEY HERE****`.
1. run `screener.ipynb` file.
1. excel file will be saved to `./output/` directory.

## Usage - custom

1. create `.env` file & save `FMP_KEY_1 = ****YOUR API KEY HERE****`.
1. create `custom.ipynb` notebook file.
1. add imports to first cell in file `from Screener import Screener`.
1. create instance of `screener = Sceener(arg= path_to_tickers.json)` object, where `path_to_tickers.json` is the location of the tickers file.
1. to execute the screener, call `screener.run(debug = False)`. Set `debug= True` if you want to see information regarding the number of stocks screened out & process remaining.
1. to view the results, call `screener.results`.
1. to create 

## Data

1. [Yahoo Finance](https://finance.yahoo.com/)
1. [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs)
