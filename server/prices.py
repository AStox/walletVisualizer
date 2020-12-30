import re
from functools import reduce

from contracts import Contracts
from utils import get_price


class PriceInfo:
    __instance = None
    @staticmethod 
    def get_instance():
        if PriceInfo.__instance == None:
            PriceInfo()
        return PriceInfo.__instance
    def __init__(self):
        if PriceInfo.__instance != None:
            raise Exception("PriceInfo already exists")
        else:
            PriceInfo.__instance = self

    prices = {}
    all_tokens = []
    liquidity_position_timestamps = {}
    liquidity_positions = {}


def is_uniswap_pool(symbol):
    return re.search(r"/", symbol) is not None

def percentChange(t1, t2):
    t1 = float(t1)
    t2 = float(t2)
    return ((t1-t2)/t2) * 100

def percent_change_calculations(transactions):
    for i, tx in enumerate(transactions[1:]):
        tx24h = transactions[i]
        tx1w = transactions[i-6]
        tx["_24hourChange"] = {}
        tx["_1weekChange"] = {}
        for _, symbol in enumerate(tx["balancesUSD"]):
            tx["_24hourChange"][symbol] = percentChange(tx["prices"][symbol], tx24h["prices"][symbol]) if tx24h["prices"].get(symbol) else None
            tx["_1weekChange"][symbol] = percentChange(tx["prices"][symbol], tx1w["prices"][symbol]) if tx1w["prices"].get(symbol) else None
        tx["_24hourChange"]["total"] = percentChange(tx["total_balance_USD"], tx24h["total_balance_USD"]) if tx24h["total_balance_USD"] else None
        tx["_1weekChange"]["total"] = percentChange(tx["total_balance_USD"], tx1w["total_balance_USD"]) if tx1w["total_balance_USD"] else None

def liquidity_returns_calculations(transactions, liquidity_returns):
    for tx in transactions:
        if liquidity_returns.get(tx["timeStamp"]):
            for _, symbol in enumerate(liquidity_returns[tx["timeStamp"]]):
                if liquidity_returns[tx["timeStamp"]][symbol]:
                    tx["balancesUSD"][symbol] = liquidity_returns[tx["timeStamp"]][symbol]["netValue"]

def sum(total, bal):
    return total + bal

def total_balance_calculations(transactions):
    for tx in transactions:
        tx["total_balance_USD"] = reduce(
            sum, tx["balancesUSD"].values(), 0
        )

def balance_calc(balances, transaction):
    contract_info = Contracts.get_instance()
    price_info = PriceInfo.get_instance()
    for i, key in enumerate(transaction["values"]):
        if not key in price_info.all_tokens:
            price_info.all_tokens.append(key)
        value = transaction["values"][key]
        balances[key] = (balances.get(key) or 0) + value
    transaction["balances"] = dict(balances)
    print(contract_info.contracts)
    for token in transaction["balances"]:
        transaction["prices"][token] = get_price(transaction["timeStamp"], token, PriceInfo.get_instance().prices)
    tempBalArrays = [
        [key, balances[key], transaction["prices"], transaction["timeStamp"], contract_info.get_contract(symbol=key).address]
        for i, key in enumerate(balances)
    ]
    usd = reduce(balancesUSD, tempBalArrays, {})
    transaction["balancesUSD"] = dict(usd)
    return balances

def balancesUSD(balances, balance_obj):
    [symbol, balance, prices_obj, timestamp, address] = balance_obj
    if is_uniswap_pool(symbol):
        if balance > 0.0000001:
            price_info = PriceInfo.get_instance()
            liquidity_position_timestamps = price_info.liquidity_position_timestamps
            liquidity_position_timestamps[timestamp] = liquidity_position_timestamps.get(timestamp) or {}
            liquidity_position_timestamps[timestamp][symbol] = [price_info.liquidity_positions[symbol]["timestamp"], timestamp, address, balance]
    else:
        balance = (balance) * float(prices_obj.get(symbol) or 0.0)
        # print(f"regular: {symbol}, price: {float(prices_obj.get(symbol) or 0.0)}, balance: {balance}")
        if balance >= 0.01:
            balances[symbol] = balance
    return balances