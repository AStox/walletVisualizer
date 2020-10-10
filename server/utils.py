import json
import datetime

prices = json.load(open("prices.json", "r"))


def get_price(timestamp, token):
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