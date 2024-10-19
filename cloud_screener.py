import asyncio
from screenerV3.alpha_module import AlphaModule
from screenerV3.beta_module import BetaModule
from time import sleep

service_account = './screener/service_account.json'
v1_path = './data/cleaned_tickers.json'
v2_path = './data/non_banking_tickers.json'
test_path = './data/test_data.json'

async def main() -> None:
  a = AlphaModule(v1_path, sheet_path= service_account)
  await a.run_async(debug= False)
  a.update_google_sheet(debug= False)
  print("Sleeping for 1 minute.")
  sleep(60)
  b = BetaModule(v2_path, sheet_path= service_account)
  await b.run_async(debug= False)
  b.update_google_sheet(debug= False)


if __name__ == "__main__":
    asyncio.run(main())
