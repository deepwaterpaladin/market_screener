# market_screener

## Setup

1. run startup file `py startup.py`.
    - this should install required dependencies & create an `.env` file.
1. within the `.env` file, replace ` # *** YOUR API KEY *** ` with your FMP API key wrapped in quotes. (i.e., `"abc123"`).
1. add your `service_account.json` file from your Google developer portal.
1. 

## Usage - application.ipynb

1. create `.env` file & save `FMP_KEY_1 = ****YOUR API KEY HERE****`.
1. add `service_account.json` file from google dev portal to `./screener/` directory.
1. run `application.ipynb` file.
1. excel file will be saved to `./output/` directory.

## Usage - custom

1. create `.env` file & save `FMP_KEY = ****YOUR API KEY HERE****`.
1. create `custom.ipynb` notebook file.
1. add imports to first cell in file `from Screener import Screener`.
1. create instance of `screener = Sceener(arg= path_to_tickers.json)` object, where `path_to_tickers.json` is the location of the tickers file.
1. to execute the screener, call `screener.run(debug = False)`. Set `debug= True` if you want to see information regarding the number of stocks screened out & process remaining.
1. to view the results, call `screener.results`.

## Data

1. [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs)
