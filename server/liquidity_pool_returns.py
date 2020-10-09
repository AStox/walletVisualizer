import requests
import json
import datetime
from web3.auto.infura import w3

prices = json.load(open("prices.json", "r"))


def round_down_datetime(timestamp):
    return int(
        datetime.datetime(
            *datetime.datetime.fromtimestamp(int(timestamp)).timetuple()[:3]
        ).timestamp()
    )


def run_query(uri, query, statusCode, headers):
    request = requests.post(uri, json={"query": query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")


def get_position(block, pair_address, token_balance):
    uri = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    wallet = "0x225ef95fa90f4F7938A5b34234d14768cB4263dd".lower()
    # block1 = 10895754
    block_timestamp = w3.eth.getBlock(block).timestamp
    day_id = int(block_timestamp / 86400)
    # pair_id = "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11".lower()
    pair_day_id = f"{pair_address.lower()}-{day_id}"
    print(pair_day_id)
    block2 = 10896140
    query = """
        {{
            pairDayData(id: "{pair_day_id}") {{
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
    query = query.format(wallet=wallet, pair_day_id=pair_day_id, block2=block2)
    statusCode = 200
    headers = {}
    results = run_query(uri, query, statusCode, headers)
    print(results)
    token0 = (
        "ETH"
        if results["data"]["pairDayData"]["token0"]["symbol"] == "WETH"
        else results["data"]["pairDayData"]["token0"]["symbol"]
    )
    token1 = (
        "ETH"
        if results["data"]["pairDayData"]["token1"]["symbol"] == "WETH"
        else results["data"]["pairDayData"]["token1"]["symbol"]
    )
    return {
        "pair": None,
        "liquidityTokenBalance": token_balance,
        "reserve0": results["data"]["pairDayData"]["reserve0"],
        "reserve1": results["data"]["pairDayData"]["reserve1"],
        "reserveUSD": results["data"]["pairDayData"]["reserveUSD"],
        "liquidityTokenTotalSupply": results["data"]["pairDayData"]["totalSupply"],
        "token0PriceUSD": prices[str(round_down_datetime(block_timestamp))][token0],
        "token1PriceUSD": prices[str(round_down_datetime(block_timestamp))][token1],
    }


print(get_position(10895754, "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11", 0))
# interface Position {
#   pair: any
#   liquidityTokenBalance: number
#   liquidityTokenTotalSupply: number
#   reserve0: number
#   reserve1: number
#   reserveUSD: number
#   token0PriceUSD: number
#   token1PriceUSD: number
# }

# def get_metric_for_position_window(positionT0, positionT1):
#     positionT0 = formatPricesForEarlyTimestamps(positionT0)
#     positionT1 = formatPricesForEarlyTimestamps(positionT1)

# #   calculate ownership at ends of window, for end of window we need original LP token balance / new total supply
#     t0Ownership = positionT0.liquidityTokenBalance / positionT0.liquidityTokenTotalSupply
#     t1Ownership = positionT0.liquidityTokenBalance / positionT1.liquidityTokenTotalSupply

# #   get starting amounts of token0 and token1 deposited by LP
#     token0_amount_t0 = t0Ownership * positionT0.reserve0
#     token1_amount_t0 = t0Ownership * positionT0.reserve1

# #   get current token values
#     token0_amount_t1 = t1Ownership * positionT1.reserve0
#     token1_amount_t1 = t1Ownership * positionT1.reserve1

# #   calculate squares to find imp loss and fee differences
#     sqrK_t0 = Math.sqrt(token0_amount_t0 * token1_amount_t0)
# #   eslint-disable-next-line eqeqeq
#     priceRatioT1 = positionT1.token0PriceUSD != 0 ? positionT1.token1PriceUSD / positionT1.token0PriceUSD : 0

#     token0_amount_no_fees = positionT1.token1PriceUSD && priceRatioT1 ? sqrK_t0 * Math.sqrt(priceRatioT1) : 0
#     token1_amount_no_fees =
#     Number(positionT1.token1PriceUSD) && priceRatioT1 ? sqrK_t0 / Math.sqrt(priceRatioT1) : 0
#     no_fees_usd =
#     token0_amount_no_fees * positionT1.token0PriceUSD + token1_amount_no_fees * positionT1.token1PriceUSD

#     difference_fees_token0 = token0_amount_t1 - token0_amount_no_fees
#     difference_fees_token1 = token1_amount_t1 - token1_amount_no_fees
#     difference_fees_usd =
#     difference_fees_token0 * positionT1.token0PriceUSD + difference_fees_token1 * positionT1.token1PriceUSD

# #   calculate USD value at t0 and t1 using initial token deposit amounts for asset return
#     assetValueT0 = token0_amount_t0 * positionT0.token0PriceUSD + token1_amount_t0 * positionT0.token1PriceUSD
#     assetValueT1 = token0_amount_t0 * positionT1.token0PriceUSD + token1_amount_t0 * positionT1.token1PriceUSD

#     imp_loss_usd = no_fees_usd - assetValueT1
#     uniswap_return = difference_fees_usd + imp_loss_usd

# #   get net value change for combined data
#     netValueT0 = t0Ownership * positionT0.reserveUSD
#     netValueT1 = t1Ownership * positionT1.reserveUSD

#   return {
#     "hodleReturn": assetValueT1 - assetValueT0,
#     "netReturn": netValueT1 - netValueT0,
#     "uniswapReturn": uniswap_return,
#     "impLoss": imp_loss_usd,
#     "fees": difference_fees_usd,
#   }