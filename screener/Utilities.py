import json

def process_tickers(path):
    """
    Processes tickers from a JSON file.

    Parameters:
    - `path` (str): The path to the JSON file containing stock tickers. Defaults to None.
    - `tickers` (dict): A dictionary of tickers. Defaults to None.

    Returns:
    - `dict`: A dictionary containing processed tickers.
    """
    t = read_json_file(path)
    clean = {
        'Japan': '.T',
        'Canada': '.TO',
        'Austria': '.VI',
        'Belgium': '.BR',
        'Estonia': '.TL',
        'France': '.PA',
        'Germany': '.DE',
        'Greece': '.AT',
        'Hungary': '.BD',
        'Italy': '.MI',
        'Latvia': '.RG',
        'Lithuania': '.VS',
        'Netherlands': '.AS',
        'Poland': '.WS',
        'Portugal': '.LS',
        'Romania': '.RO',
        'Finland': '.HE',
        'Spain': '.MC',
        'Sweden': '.ST',
        'Switzerland': '.SW',
        'United Kingdom': '.L',
        'New Zealand': '.NZ',
        'Czech Republic': '.PR',
        'USA': ''}

    return t


def read_json_file(path) -> dict[str:list]:
    """
    Reads a JSON file and returns its content as a dictionary.

    Parameters:
    - `file_path` (str): The path to the JSON file.

    Returns:
    - `dict`: A dictionary containing the content of the JSON file.
    """
    with open(path, 'r') as file:
        data = json.load(file)
    return data