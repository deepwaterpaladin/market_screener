import pytest
import pandas as pd
from screener.AsyncScreener2 import AsyncScreener2


@pytest.fixture
def screener():
    screener = AsyncScreener2(ticker_path="./test_tickers.json")
    return screener

def test_pafcf(screener):
    screener.results = {
        "AAPL": {"Name": "Apple Inc.", "NCAV Ratio": 1.5, "P/aFCF Ratio": 11, "EV/aFCF": 3.5, "P/TBV Ratio": 0.9},
        "GOOGL": {"Name": "Google LLC", "NCAV Ratio": 1.7, "P/aFCF Ratio": 1.8, "EV/aFCF": 4.0, "P/TBV Ratio": 1.2}
    }
    
    assert(len(screener.results) == 2)
    screener.check_pafcf()
    assert(len(screener.results) == 1)

def test_pafcf_no_drop(screener):
    screener.results = {
        "AAPL": {"Name": "Apple Inc.", "NCAV Ratio": 1.5, "P/aFCF Ratio": 10, "EV/aFCF": 3.5, "P/TBV Ratio": 0.9},
        "GOOGL": {"Name": "Google LLC", "NCAV Ratio": 1.7, "P/aFCF Ratio": 1.8, "EV/aFCF": 4.0, "P/TBV Ratio": 1.2}
    }
    
    assert(len(screener.results) == 2)
    screener.check_pafcf()
    assert(len(screener.results) == 2)

def test_clean_results_drops_non_isAdded(screener):
    screener.results = {
        "AAPL": {"Name": "Apple Inc.", "NCAV Ratio": 1.5, "P/aFCF Ratio": 10, "EV/aFCF": 3.5, "P/TBV Ratio": 0.9, "isAdded":False},
        "GOOGL": {"Name": "Google LLC", "NCAV Ratio": 1.7, "P/aFCF Ratio": 1.8, "EV/aFCF": 4.0, "P/TBV Ratio": 1.2, "isAdded":True}
    }

    assert(len(screener.results) == 2)
    screener.clean_results()
    assert(len(screener.results) == 1)

def test_clean_results_keeps_isAdded(screener):
    screener.results = {
        "AAPL": {"Name": "Apple Inc.", "NCAV Ratio": 1.5, "P/aFCF Ratio": 10, "EV/aFCF": 3.5, "P/TBV Ratio": 0.9, "isAdded":True},
        "GOOGL": {"Name": "Google LLC", "NCAV Ratio": 1.7, "P/aFCF Ratio": 1.8, "EV/aFCF": 4.0, "P/TBV Ratio": 1.2, "isAdded":True}
    }

    assert(len(screener.results) == 2)
    screener.clean_results()
    assert(len(screener.results) == 2)

def test_clean_results_drops_blacklist(screener):
    screener.industry_blacklist_tickers.append("AAPL")
    screener.results = {
        "AAPL": {"Name": "Apple Inc.", "NCAV Ratio": 1.5, "P/aFCF Ratio": 10, "EV/aFCF": 3.5, "P/TBV Ratio": 0.9, "isAdded":True},
        "GOOGL": {"Name": "Google LLC", "NCAV Ratio": 1.7, "P/aFCF Ratio": 1.8, "EV/aFCF": 4.0, "P/TBV Ratio": 1.2, "isAdded":True}
    }

    assert(len(screener.results) == 2)
    screener.clean_results()
    assert(len(screener.results) == 1)


def test_previous_seen_tickers(screener):
    assert(len(screener.previous) != 0)

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