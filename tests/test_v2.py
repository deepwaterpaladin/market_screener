import pytest
import pandas as pd
import asyncio
from screener.AsyncScreener2 import AsyncScreener2
import json


@pytest.fixture
def screener():
    # Load tickers from a test file
    with open("./test_tickers.json") as f:
        tickers = json.load(f)
    
    # Initialize the AsyncScreener2 instance with mock paths
    screener = AsyncScreener2(ticker_path=tickers, sheet_path="dummy_sheet_path.json", sheet_name="Test Sheet")
    return screener


@pytest.fixture
def mock_floats():
    return [
        {"symbol": "AAPL", "outstandingShares": 17000000000},
        {"symbol": "GOOGL", "outstandingShares": 3000000000},
        {"symbol": "TSLA", "outstandingShares": 1000000000}
    ]


@pytest.fixture
def mock_data():
    return {
        "company_data": [
            {"companyName": "Apple Inc.", "country": "US", "industry": "Technology"},
            {"companyName": "Google LLC", "country": "US", "industry": "Technology"},
            {"companyName": "Tesla Inc.", "country": "US", "industry": "Automotive"}
        ],
        "market_data": [
            {"marketCapTTM": 2000000000, "freeCashFlowPerShareTTM": 1.0, "enterpriseValueTTM": 2500000000, "tangibleAssetValueTTM": 500000000},
            {"marketCapTTM": 3000000000, "freeCashFlowPerShareTTM": 2.0, "enterpriseValueTTM": 3500000000, "tangibleAssetValueTTM": 700000000},
            {"marketCapTTM": 1500000000, "freeCashFlowPerShareTTM": 1.5, "enterpriseValueTTM": 1800000000, "tangibleAssetValueTTM": 400000000}
        ],
        "balance_data": [
            {"totalCurrentAssets": 5000000000, "totalLiabilities": 2000000000},
            {"totalCurrentAssets": 6000000000, "totalLiabilities": 3000000000},
            {"totalCurrentAssets": 4000000000, "totalLiabilities": 1500000000}
        ],
        "cashflow_data": [
            {"freeCashFlow": 1000000000},
            {"freeCashFlow": 2000000000},
            {"freeCashFlow": 1200000000}
        ]
    }


@pytest.mark.asyncio
async def test_run_async(screener, mock_floats, mock_data):
    # Manually set the floats
    screener.floats = mock_floats

    # Mock the API responses by overriding the __handle_screener2 method
    async def mock_handle_screener(tickers, debug=False):
        for i, ticker in enumerate(tickers):
            screener.results[ticker] = {
                "Name": mock_data["company_data"][i]["companyName"],
                "NCAV Ratio": mock_data["balance_data"][i]["totalCurrentAssets"] / mock_data["balance_data"][i]["totalLiabilities"],
                "P/aFCF Ratio": mock_data["market_data"][i]["marketCapTTM"] / (mock_data["cashflow_data"][i]["freeCashFlow"] / mock_floats[i]["outstandingShares"]),
                "EV/aFCF": mock_data["market_data"][i]["enterpriseValueTTM"] / (mock_data["cashflow_data"][i]["freeCashFlow"]),
                "P/TBV Ratio": mock_data["market_data"][i]["marketCapTTM"] / mock_data["market_data"][i]["tangibleAssetValueTTM"]
            }

    screener.__handle_screener2 = mock_handle_screener

    # Run the async method
    await screener.run_async(batch_size=3)

    # Validate that the screening results are as expected
    assert len(screener.results) == 3
    assert screener.results["AAPL"]["NCAV Ratio"] == 2.5
    assert screener.results["AAPL"]["P/aFCF Ratio"] == 1.3
    assert screener.results["AAPL"]["EV/aFCF"] == 2.5
    assert screener.results["AAPL"]["P/TBV Ratio"] == 4.0


def test_create_xlsx(screener):
    # Manually set the results to be exported
    screener.results = {
        "AAPL": {"Name": "Apple Inc.", "NCAV Ratio": 1.5, "P/aFCF Ratio": 2.0, "EV/aFCF": 3.5, "P/TBV Ratio": 0.9},
        "GOOGL": {"Name": "Google LLC", "NCAV Ratio": 1.7, "P/aFCF Ratio": 1.8, "EV/aFCF": 4.0, "P/TBV Ratio": 1.2}
    }

    # Simulate the call to create_xlsx
    screener.create_xlsx(file_path="test_results.xlsx")

    # Read the created file to ensure data was correctly written
    df = pd.read_excel("test_results.xlsx")
    assert "Name" in df.columns
    assert len(df) == 2
    assert df.loc[0, "Name"] == "Apple Inc."
    assert df.loc[1, "Name"] == "Google LLC"