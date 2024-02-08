# market_screener

## Project Requirements (High Level)

1. Market Cap at or below Net-Current-Asset-Value
1. Average 5Y annual Free Cash Flow > 10%
1. Positive TTM Free-cashflow
1. Zero or negative net-debt
1. Some 5Y dividends or buybacks present
1. Only companies from selected country HQs or exchanges
1. Run weekly; saving results to a .xlsx db

## Usage

1. create `.env` file & save `FMP_KEY_1 = ****YOUR API KEY HERE****`.
1. run `screener.ipynb` file.

## Data

1. [Yahoo Finance](https://finance.yahoo.com/)
1. [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs)
