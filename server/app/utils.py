import json
import datetime
import requests

# prices = json.load(open("prices.json", "r"))


def get_price(timestamp, token, prices):
    if n := prices.get(str(round_down_datetime(timestamp))):
        if p := n.get(token):
            return float(p)
    return float(0)


def round_down_datetime(timestamp):
    return int(
        datetime.datetime(
            *datetime.datetime.fromtimestamp(int(timestamp)).timetuple()[:3]
        ).timestamp()
    )

def run_query(uri, query, statusCode, headers, name=None):
    request = requests.post(uri, json={"query": query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"{name}: {request}")