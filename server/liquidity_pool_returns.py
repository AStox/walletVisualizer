import requests
import time
import sys
import json
import datetime
import math
from web3.auto.infura import w3
from utils import get_price, round_down_datetime

prices = json.load(open("prices.json", "r"))


def run_query(uri, query, statusCode, headers):
    request = requests.post(uri, json={"query": query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(request)


def get_positions(timestamp1, timestamp2, pair_address, token_balance):
    uri = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    day_id1 = int(timestamp1 / 86400)
    pair_day_id1 = f"{pair_address.lower()}-{day_id1}"
    day_id2 = int(timestamp2 / 86400)
    pair_day_id2 = f"{pair_address.lower()}-{day_id2}"
    query = """
        {{
            position1: pairDayData(id: "{pair_day_id1}") {{
                date
                pairAddress
                token0 {{
                    symbol
                }}
                token1 {{
                    symbol
                }}
                reserve0
                reserve1
                totalSupply
                reserveUSD
            }}
            position2: pairDayData(id: "{pair_day_id2}") {{
                date
                pairAddress
                token0 {{
                    symbol
                }}
                token1 {{
                    symbol
                }}
                reserve0
                reserve1
                totalSupply
                reserveUSD
            }}
        }}
        """
    query = query.format(pair_day_id1=pair_day_id1, pair_day_id2=pair_day_id2)
    statusCode = 200
    headers = {}
    attempt = 0
    results = run_query(uri, query, statusCode, headers)
    if (
        not results.get("data")
        or not results["data"].get("position1")
        or not results["data"].get("position2")
    ):
        return None
    token0 = (
        "ETH"
        if results["data"]["position1"]["token0"]["symbol"] == "WETH"
        else results["data"]["position1"]["token0"]["symbol"]
    )
    token1 = (
        "ETH"
        if results["data"]["position1"]["token1"]["symbol"] == "WETH"
        else results["data"]["position1"]["token1"]["symbol"]
    )
    return [
        {
            "pair": None,
            "timestamp": int(timestamp1),
            "liquidityTokenBalance": float(token_balance),
            "reserve0": float(results["data"]["position1"]["reserve0"]),
            "reserve1": float(results["data"]["position1"]["reserve1"]),
            "reserveUSD": float(results["data"]["position1"]["reserveUSD"]),
            "liquidityTokenTotalSupply": float(
                results["data"]["position1"]["totalSupply"]
            ),
            "token0PriceUSD": get_price(timestamp1, token0),
            "token1PriceUSD": get_price(timestamp1, token1),
        },
        {
            "pair": None,
            "timestamp": int(timestamp2),
            "liquidityTokenBalance": float(token_balance),
            "reserve0": float(results["data"]["position2"]["reserve0"]),
            "reserve1": float(results["data"]["position2"]["reserve1"]),
            "reserveUSD": float(results["data"]["position2"]["reserveUSD"]),
            "liquidityTokenTotalSupply": float(
                results["data"]["position2"]["totalSupply"]
            ),
            "token0PriceUSD": get_price(timestamp2, token0),
            "token1PriceUSD": get_price(timestamp2, token1),
        },
    ]


# interface Position {
#   pair: any
#   liquidityTokenBalance: number
#   liquidityTokenTotalSupply: number
#   reserve0: number
#   reserve1: number
#   reserveUSD: number
#   token0PriceUSD: number
#   token1PriceUSD: number
#   timestamp: number
# }


def get_metric_for_position_window(positionT0, positionT1):

    #   calculate ownership at ends of window, for end of window we need original LP token balance / new total supply
    t0Ownership = (
        positionT0["liquidityTokenBalance"] / positionT0["liquidityTokenTotalSupply"]
    )
    t1Ownership = (
        positionT0["liquidityTokenBalance"] / positionT1["liquidityTokenTotalSupply"]
    )

    #   get starting amounts of token0 and token1 deposited by LP
    token0_amount_t0 = t0Ownership * positionT0["reserve0"]
    token1_amount_t0 = t0Ownership * positionT0["reserve1"]

    #   get current token values
    token0_amount_t1 = t1Ownership * positionT1["reserve0"]
    token1_amount_t1 = t1Ownership * positionT1["reserve1"]

    #   calculate squares to find imp loss and fee differences
    sqrK_t0 = math.sqrt(token0_amount_t0 * token1_amount_t0)

    priceRatioT1 = (
        positionT1["token1PriceUSD"] / positionT1["token0PriceUSD"]
        if positionT1["token0PriceUSD"] != 0
        else 0
    )

    token0_amount_no_fees = (
        sqrK_t0 * math.sqrt(priceRatioT1)
        if positionT1["token1PriceUSD"] and priceRatioT1
        else 0
    )
    token1_amount_no_fees = (
        sqrK_t0 / math.sqrt(priceRatioT1)
        if positionT1["token1PriceUSD"] and priceRatioT1
        else 0
    )
    no_fees_usd = (
        token0_amount_no_fees * positionT1["token0PriceUSD"]
        + token1_amount_no_fees * positionT1["token1PriceUSD"]
    )

    difference_fees_token0 = token0_amount_t1 - token0_amount_no_fees
    difference_fees_token1 = token1_amount_t1 - token1_amount_no_fees
    difference_fees_usd = (
        difference_fees_token0 * positionT1["token0PriceUSD"]
        + difference_fees_token1 * positionT1["token1PriceUSD"]
    )

    #   calculate USD value at t0 and t1 using initial token deposit amounts for asset return
    assetValueT0 = (
        token0_amount_t0 * positionT0["token0PriceUSD"]
        + token1_amount_t0 * positionT0["token1PriceUSD"]
    )
    assetValueT1 = (
        token0_amount_t0 * positionT1["token0PriceUSD"]
        + token1_amount_t0 * positionT1["token1PriceUSD"]
    )

    imp_loss_usd = no_fees_usd - assetValueT1
    uniswap_return = difference_fees_usd + imp_loss_usd

    #   get net value change for combined data
    netValueT0 = t0Ownership * positionT0["reserveUSD"]
    netValueT1 = t1Ownership * positionT1["reserveUSD"]

    return {
        "hodleValue": assetValueT1,
        "netValue": netValueT1,
        "hodleReturn": assetValueT1 - assetValueT0,
        "netReturn": netValueT1 - netValueT0,
        "uniswapReturn": uniswap_return,
        "impLoss": imp_loss_usd,
        "fees": difference_fees_usd,
    }


def get_returns_windows(timestamp1, timestamp2, pair_address, token_balance):
    positions = get_positions(
        int(timestamp1), int(timestamp2), pair_address, token_balance
    )
    if not positions:
        return None
    return get_metric_for_position_window(positions[0], positions[1])

def get_batched_query(timestamp, pair_address, query_id):
    day_id1 = int(int(timestamp) / 86400)
    pair_day_id1 = f"{pair_address.lower()}-{day_id1}"
    new_query = """
        
            {query_id}: pairDayData(id: "{pair_day_id1}") {{
                date
                pairAddress
                token0 {{
                    symbol
                }}
                token1 {{
                    symbol
                }}
                reserve0
                reserve1
                totalSupply
                reserveUSD
            }}
        """
    new_query = new_query.format(pair_day_id1=pair_day_id1, query_id=query_id)
    return new_query
    

def get_batched_positions(batched_data):
    index = 0
    index_map = {}
    start_timestamps = []
    token_balance = {}
    query = """
        {
        """
    for i, timestamp in enumerate(batched_data):
        symbol_data = batched_data[timestamp]
        index_map[timestamp] = index_map.get(timestamp) or {}
        for j, symbol in enumerate(symbol_data):
            args = symbol_data[symbol]
            index_map[timestamp][symbol] = index_map[timestamp].get(symbol) or {}
            if not args[0] in start_timestamps:
                query_id = f"position{index}"
                index_map[timestamp][symbol]["start"] = index
                query += (get_batched_query(args[0], args[2], query_id))
                token_balance[query_id] = (args[3])
                index += 1
            else:
                index_map[timestamp][symbol]["start"] = start_timestamps.index(args[0])
            query_id = f"position{index}"
            index_map[timestamp][symbol]["end"] = index
            query += (get_batched_query(args[1], args[2],query_id))
            token_balance[query_id] = (args[3])
            index += 1
    query += ("""
        }
        """)
    statusCode = 200
    headers = {}
    uri = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    results = run_query(uri, query, statusCode, headers)
    if not results.get("data"):
        print(results)
        return None
    positions = {}
    for ind, query_id in enumerate(results["data"]):
        position = results["data"][query_id]
        if not position:
            positions[query_id] = None
        else:
            token0 = (
                "ETH"
                if position["token0"]["symbol"] == "WETH"
                else position["token0"]["symbol"]
            )
            token1 = (
                "ETH"
                if position["token1"]["symbol"] == "WETH"
                else position["token1"]["symbol"]
            )
            positions[query_id] = {
                "pair": f"{token0}/{token1}",
                "timestamp": int(position["date"]),
                "liquidityTokenBalance": float(token_balance[query_id]),
                "reserve0": float(position["reserve0"]),
                "reserve1": float(position["reserve1"]),
                "reserveUSD": float(position["reserveUSD"]),
                "liquidityTokenTotalSupply": float(
                    position["totalSupply"]
                ),
                "token0PriceUSD": get_price(int(position["date"]), token0),
                "token1PriceUSD": get_price(int(position["date"]), token1),
            }
    return [positions, index_map]

def get_batched_returns(batched_data):
    [positions, index_map] = get_batched_positions(batched_data);
    batched_returns = {}
    for _, timestamp in enumerate(index_map):
        batched_returns[timestamp] = batched_returns.get("timestamp") or {}
        for _, symbol in enumerate(index_map[timestamp]):
            position0 = positions[f"position{index_map[timestamp][symbol]['start']}"]
            position1 = positions[f"position{index_map[timestamp][symbol]['end']}"]
            if position0 and position1:
                batched_returns[timestamp][symbol] = get_metric_for_position_window(position0, position1)
            else:
                batched_returns[timestamp][symbol] = None
    
    return batched_returns


