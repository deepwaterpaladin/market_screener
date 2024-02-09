import json

def read_json_file(file_path) ->list[str]:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def write_json_file(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def is_whitelist_nation(country: str) -> bool:
    countries = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
    'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
    'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands',
    'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden',
    'USA', 'United States', 'Canada', 'United Kingdom', 'UK', 'Japan', 'Australia']
    return country in countries