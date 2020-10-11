import requests
import time
import sys
import json
import datetime
import math
from web3.auto.infura import w3
from utils import get_price, round_down_datetime

prices = json.load(open("prices.json", "r"))

ATTEMPTS = 1


def run_query(uri, query, statusCode, headers):
    request = requests.post(uri, json={"query": query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")


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
    print(query)
    print(results)
    print("----------------")
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