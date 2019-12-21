# configuration

import json

def load_config():
    data = None
    with open('.profile/accounts.json') as json_data_file:
        data = json.load(json_data_file)
    return data
