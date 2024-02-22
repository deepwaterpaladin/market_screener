import asyncio
from screener.AsyncScreener import AsyncScreener

ticker_path = "./data/cleaned_tickers.json"
service_account_path = "./screener/service_account.json"
sheet_name = "Screener"


async def main() -> None:
    screener = AsyncScreener(ticker_path, service_account_path, sheet_name)
    await screener.run_async()
    screener.update_google_sheet()

if __name__ == "__main__":
    asyncio.run(main())