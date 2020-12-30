import requests
import time
import sys
import json
import datetime
import math
from web3.auto.infura import w3
from contracts import Contracts
from utils import get_price, round_down_datetime, run_query

BATCH_SIZE = 10

def get_batched_query(timestamp, symbol, address):
    day_id = int(int(timestamp) / 86400)
    # pair_address = contracts[symbol.replace('_','/')]["address"]
    pair_address = address
    pair_day_id = f"{pair_address.lower()}-{day_id}"
    new_query ="""             tokendaydata{timestamp}{symbol}:tokenDayData(id: "{pair_day_id}") {{
                date
                token {{
                    symbol
                }}
                dailyVolumeToken
                dailyVolumeETH
                dailyVolumeUSD
                dailyTxns
                totalLiquidityToken
                totalLiquidityETH
                totalLiquidityUSD
                priceUSD
                maxStored
            }}
    """
    new_query = new_query.format(pair_day_id=pair_day_id, timestamp=timestamp, symbol=symbol)
    return new_query
    

def get_batched_token_day_data(batched_data, index):
    contracts_info = Contracts.get_instance()
    positions = {}
    index_map = {}
    query = """
        {
        """
    for i, timestamp in enumerate(batched_data):
        symbol_data = batched_data[timestamp]
        index_map[timestamp] = index_map.get(timestamp) or {}
        for j, symbol in enumerate(symbol_data):
            index_map[timestamp][symbol] = index
            symbols = symbol.split('_')
            if (len(symbols) > 1):
                address1 = contracts_info.get_contract(symbol=symbols[0]).address
                address2 = contracts_info.get_contract(symbol=symbols[1]).address
                address = contracts_info.fetch_uniswap_pool_contract(address1, address2).address
            else:
                address = contracts_info.get_contract(symbol=symbol).address
            query += (get_batched_query(timestamp, symbol, address))
            index += 1
    query += ("""
        }""")
    statusCode = 200
    headers = {}
    uri = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    results = run_query(uri, query, statusCode, headers, "price_fetcher")
    if not results.get("data"):
        raise Exception(results)
    return [results["data"], index_map, index]

def get_batched_prices(batched_data, tokens):
    token_day_data = {}
    index_map = {}
    index = 0
    count = math.ceil(len(batched_data) / BATCH_SIZE)
    keys = list(batched_data.keys())
    for i in range(0, count):
        if i == count-1:
            batch = {}
            for j in range(i*BATCH_SIZE, i*BATCH_SIZE + (len(batched_data) - i*BATCH_SIZE)):
                batch[keys[j]] = batched_data[keys[j]]
        else:    
            batch = {}
            for j in range(i*BATCH_SIZE, (i+1) * BATCH_SIZE):
                batch[keys[j]] = batched_data[keys[j]]
        [batched_token_day_data, batched_index_map, new_index] = get_batched_token_day_data(batch, index);
        index = new_index
        token_day_data = {**token_day_data, **batched_token_day_data}
        index_map = {**index_map, **batched_index_map}
    batched_prices = {}
    for _, timestamp in enumerate(batched_data):
        timestamp = str(timestamp)
        batched_prices[timestamp] = batched_prices.get("timestamp") or {}
        for _, symbol in enumerate(tokens):
            token_day_datum = token_day_data[f"tokendaydata{timestamp}{symbol}"]
            if token_day_datum:
                symbol = symbol.replace('_','/')
                # symbol = "ETH" if symbol == "WETH" else symbol
                batched_prices[timestamp][symbol] = token_day_datum['priceUSD']
    return batched_prices

def fetch_price_data(transactions):
    tokens = []
    data = {}
    for tx in transactions:
        for _, symbol in enumerate(tx["values"]):
            if not symbol in tokens:
                # symbol = "WETH" if symbol == "ETH" else symbol
                tokens.append(symbol.replace('/','_'))
    for tx in transactions:
        data[round_down_datetime(tx["timeStamp"])] = { symbol: 0 for symbol in tokens }
    return get_batched_prices(data, tokens)
    