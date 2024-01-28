from playwright.sync_api import Playwright, sync_playwright, expect, TimeoutError
import json
import pandas as pd

def extract_stock_symbols(page):
    # Wait for the table to be rendered (you may need to adjust the waiting time)
    page.wait_for_selector('table.symbol-table tbody')

    # Extract stock symbols from the table
    symbols = page.evaluate('''() => {
        const tbody = document.querySelector('table.symbol-table tbody');
        const symbols = [];
        for (const row of tbody.children) {
            const symbol = row.querySelector('.sym a').innerText;
            symbols.push(symbol);
        }
        return symbols;
    }''')

    return symbols


def is_locator_present(page):
    try:
        page.locator("text=Stay informed in just 2 minutes Get an email with the top market-moving news in ")
        page.locator("[aria-label=\"Close\"]").click()
        print("Closing popup")
    except:
        pass
    
def get_data(set_data:set) -> None:
    json_file_name = "tickers.json"
    with open(json_file_name, 'w') as json_file:
        json.dump(list(set_data), json_file)
    print(f"Set converted to JSON and saved to '{json_file_name}'.")


def run(playwright: Playwright) -> set():
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    # Open new page
    symbols = set()
    page = context.new_page()
    # Go to https://stockanalysis.com/stocks/screener/
    page.goto("https://stockanalysis.com/stocks/screener/")
    # is_locator_present(page)
    # Click text=Symbol
    page.locator("text=Symbol").click()
    # Click text=Symbol
    page.locator("text=Symbol").click()
    # is_locator_present(page)
    # Click button:has-text("20 Rows")
    page.locator("button:has-text(\"20 Rows\")").click()
    # Click text=50 Rows
    page.locator("text=50 Rows").click()
    page.pause() # pausing to self filter
    for i in range(1, 94):
        try:
            # is_locator_present(page)
            # Extract stock symbols
            stock_symbols = extract_stock_symbols_V2(page)
            # stock_symbols = extract_stock_symbols(page)
            print(stock_symbols)
            page.pause()
            page.locator("button:has-text(\"Next\")").click(timeout=1000)
            for sym in stock_symbols:
                symbols.add(sym)
        except:
            break

    # ---------------------
    print(len(symbols))
    # get_data(symbols)
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)