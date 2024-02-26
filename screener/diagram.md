# Market Screener Class Breakdown

## AsyncScreener Class

The `AsyncScreener` class is responsible for screening stock tickers asynchronously. Let's break down its functionalities:

### Constructor

- `__init__`
  - `ticker_path`: Path to the JSON file containing stock tickers.
  - `sheet_path`: Path to the Google Service Account JSON file. Defaults to ./service_account.json.
  - `sheet_name`: Name of the Google Sheet. Defaults to Screener.

### Public Methods

1. `run_async`:
   - Asynchronously runs the screening process.
1. `create_xlsx`:
   - Creates an Excel file with the screening results.
1. `update_google_sheet`:
   - Updates a Google Sheet with the screening results.

### Private Methods

1. `__read_json_file`:
   - Reads a JSON file and returns its content as a dictionary.
   - Private method.
1. `__process_tickers`:
   - Processes tickers from a JSON file.
   - Private method.
1. `__sort_results_dict`(self) -> None:
   - Sorts the results dictionary by "NCAV Ratio" and then by "Payback Rating".
   - Private method.
1. `__remove_previously_seen`(self) -> list[str]:
   - Removes tickers that have been previously seen in Google Sheets.
   - Private method.
1. `__calculate_packback_rating`(self, debug: bool = False) -> None:
   - Calculates the payback rating for the screening results.
   - Private method.
1. `__get_data`
   - Method for fetching financial data from FMP API asynchronously.
   - Calls `__get_profile`, `__get_cashflow`, & `__get_balance_sheet`.
1. `__get_profile`:
   - Method for fetching financial profile from FMP API asynchronously.
1. `__get_cashflow`:
   - Method for fetching financial data from FMP API asynchronously.
1. `__get_balance_sheet`:
   - Method for fetching financial data from FMP API asynchronously.
1. `__handle_tickers`: Handles ticker data asynchronously in batches.

## Sheet Class

### Constructor

- `__init__`
  - `sheet_path`: Path to the Google Service Account JSON file. Defaults to ./service_account.json.
  - `file_name`: Name of the Google Sheet. Defaults to Screener.

### Public Methods

1. `add_row_data`:
   - Adds row data to the Google Sheet.
1. `get_all_worksheets`:
   - Retrieves all worksheets from the Google Sheet.
1. `create_new_tab`:
   - Creates a new tab in the Google Sheet.
1. `get_previously_seen_tickers`:
   - Retrieves tickers seen in the previous session.
1. `get_all_previously_seen_tickers`:
   - Retrieves all tickers seen in the last year (52 weeks).

### Private Methods

1. `__get_worksheet_names`:
   - Returns all worksheet names in a given workbook.
1. `__extract_date_from_string`:
   - Gets the date of the most recent screener execution.
1. `__add_header`:
   - Appends header row to Google Workbook sheet.
