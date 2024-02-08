from playwright.sync_api import Playwright, sync_playwright
import json
import time

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

def select_country(page):
    countries = ['Japan', 'Canada','Austria', 'Belgium','Estonia','France', 'Germany', 'Greece', 'Hungary', 'Italy', 
                'Latvia', 'Lithuania','Netherlands','Poland', 'Portugal', 'Romania', 'Finland', 
                'Spain', 'Sweden', 'Switzerland', 'United Kingdom', 'New Zealand', 'Russia', 'Czech Republic']
    c_dict = {}
    page.locator(".tv-screener-market-select").click()
    for country in countries:
        page.locator(f"text={country}").click()
        page.locator("button:has-text(\"Apply\")").click()
        time.sleep(2)
        matches_value = page.inner_text('.js-field-total')
        end = int(matches_value.split(' ')[0])
        print(f"{end} matches for {country}")
        for i in range(0,end, 50):
            scroll_to_bottom_and_wait(page)
        c_dict[country] = extract_stock_symbolsV2(page)
        print(f'{len(c_dict[country])} tickers added for {country}')
        page.locator(".tv-screener-market-select").click()
    return c_dict


def get_data(data:dict, name:str="ticker") -> None:
    json_file_name = f"{name}.json"
    with open(json_file_name, 'w') as json_file:
        json.dump(data, json_file)
    print(f"Set converted to JSON and saved to '{json_file_name}'.")

def extract_stock_symbolsV2(page) -> list:
    # Wait for the table to be present on the page
    page.wait_for_selector('.tv-data-table__row')
    
    # Extract stock symbols
    symbols = page.evaluate('''() => {
        const symbolElements = document.querySelectorAll('.tv-data-table__row');
        // const arr = Array.from(symbolElements, element => element.getAttribute('data-field-key'))
        return Array.from(symbolElements, element => element.getAttribute('data-symbol'));
    }''')

    return symbols

def is_locator_present(page):
    try:
        page.locator("text=Stay informed in just 2 minutes Get an email with the top market-moving news in ")
        page.locator("[aria-label=\"Close\"]").click()
        print("Closing popup")
    except:
        pass
    
def scroll_to_bottom_and_wait(page):
    page.evaluate('''async () => {
        // Scroll to the bottom of the page
        window.scrollTo(0, document.body.scrollHeight);

        // Wait for the page to load more content (you may need to adjust the delay based on your specific case)
        await new Promise(resolve => setTimeout(resolve, 5000));
    }''')

def run2(playwright: Playwright) -> set():
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    # Open new page
    symbols = set()
    page = context.new_page()
    page.goto("https://www.tradingview.com/screener/")
    # Click .close-B02UUUN3
    page.locator(".close-B02UUUN3").click()
    fin = select_country(page)
    # tickers = extract_stock_symbolsV2(page)
    # print(tickers)
    # page.pause()
    # for i in range(1, 206):
    #     scroll_to_bottom_and_wait(page)
    #     time.sleep(2.5)
    #     if i % 10 == 0:
    #         print(f"{206-i} reloads remaining...")
    # fin = extract_stock_symbolsV2(page)
    get_data(fin, "init")


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
    run2(playwright)