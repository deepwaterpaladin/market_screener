import requests

OperatingExpenses = f"https://data.sec.gov/api/xbrl/frames/us-gaap/OperatingExpenses/USD/CY2022.json"
NetCashProvidedByUsedInOperatingActivities = f"https://data.sec.gov/api/xbrl/frames/us-gaap/NetCashProvidedByUsedInOperatingActivities/USD/CY2022.json"

def convert_cik_list(file_path: str) -> dict:
    result_dict = {}
    
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(':')
            if len(parts) == 2:
                ticker = parts[0].strip().upper()
                value = int(parts[1].strip())
                result_dict[ticker] = value
    
    return result_dict