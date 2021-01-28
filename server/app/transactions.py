import datetime

from functools import reduce
from app.prices import PriceInfo
from app.utils import get_price, round_down_datetime

def sortTransactions(e):
    return int(e["timeStamp"])

def days_between_transactions(timestamp1, timestamp2):
    return range(0, int((int(timestamp2) - int(timestamp1))/ (60 * 60 * 24)))

def timestamps_between_transactions(timestamp1, timestamp2):
    return [j * 60 * 60 * 24 + int(timestamp1) for j in days_between_transactions(timestamp1, timestamp2)]

def fill_out_dates(transactions):
    fill_dates = []
    prices = PriceInfo.get_instance().prices
    # Filling in dates up to the last transaction
    for tx_index, tx in enumerate(transactions[0:-1]):
        for i in timestamps_between_transactions(transactions[tx_index]["timeStamp"], transactions[tx_index + 1]["timeStamp"]):
            values = {}
            token_prices = {}
            if transactions[tx_index].get("values", None):
                for key, value in transactions[tx_index]["values"].items():
                    values[key] = 0
                    token_prices[key] = get_price(i, key, PriceInfo.get_instance().prices)
            fill_dates.append(
                {
                    "timeStamp": i,
                    "values": values,
                    "prices": token_prices,
                    "isError": 0,
                }
            )

    # Filling in dates from the last transaction until now
    now_timestamp = datetime.datetime(*datetime.datetime.utcnow().timetuple()[:3]).timestamp()
    for i in timestamps_between_transactions(transactions[-1]["timeStamp"], now_timestamp):
        values = {}
        token_prices = {}
        if transactions[tx_index].get("values", None):
            for key, value in transactions[-1]["values"].items():
                values[key] = 0
                token_prices[key] = get_price(i, key, prices)
        fill_dates.append(
            {"timeStamp": i, "values": values, "prices": token_prices, "isError": 0}
        )
    # FIXME: This is using local time, but tx timestamps are in UTC. This should changed to UTC
    # and timezone conversion should be done later or on the frontend
    now = int(datetime.datetime.now().timestamp())
    values = {}
    token_prices = {}
    if transactions[tx_index].get("values", None):
        for key, value in transactions[-1]["values"].items():
                values[key] = 0
                token_prices[key] = get_price(now, key, prices)
    fill_dates.append(
        {"timeStamp": now, "values": values, "prices": token_prices, "isError": 0}
    )
    for i in fill_dates:
        transactions.append(i)
    transactions.sort(key=sortTransactions)

    return transactions


def group_by_date(transactions):
    grouped_tx = {}
    for tx in transactions:
        timestamp = str(round_down_datetime(tx["timeStamp"]))
        if grouped_tx.get(timestamp):
            grouped_tx[timestamp]["transactions"].append(tx)
        else:
            grouped_tx[timestamp] = {"transactions": [tx]}

    grouped_array = []
    for i, timestamp in enumerate(grouped_tx):
        grouped_tx[timestamp]["prices"] = PriceInfo.get_instance().prices.get(timestamp) or {}
        grouped_tx[timestamp]["timeStamp"] = timestamp
        grouped_tx[timestamp]["values"] = reduce(
            sum_values, grouped_tx[timestamp]["transactions"], {}
        )
        grouped_array.append(grouped_tx[timestamp])
    grouped_array[-1]["timeStamp"] = transactions[-1]["timeStamp"]    #the last date is now and should not be rounded down

    return grouped_array

def sum_values(sum, tx):
    values = sum
    for i, key in enumerate(tx["values"]):
        if int(tx["isError"]) == 0:
            values[key] = (sum.get(key) or 0) + tx["values"][key]
    return dict(values)