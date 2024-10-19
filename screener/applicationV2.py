import asyncio
from screener.AsyncScreener2 import AsyncScreener2

service_account = './screener/service_account.json'
path = './data/non_banking_tickers.json'

async def main() -> None:
    screener2 =  AsyncScreener2(path, sheet_path = service_account)
    await screener2.run_async(batch_size= 75)
    screener2.update_google_sheet()

if __name__ == "__main__":
    asyncio.run(main())
