import requests


def run_query(uri, query, statusCode, headers):
    request = requests.post(uri, json={"query": query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")


uri = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
wallet = "0x225ef95fa90f4F7938A5b34234d14768cB4263dd".lower()
query = """
    {{
        user(id: "{wallet}") {{
            id
            liquidityPositions {{
                pair {{
                    token0 {{
                        name
                    }}
                    token1{{
                        name
                    }}
                }}
                liquidityTokenBalance
            }}
        }}
    }}
    """
query = query.format(wallet=wallet)
print(query)
statusCode = 200
headers = {}
results = run_query(uri, query, statusCode, headers)
print(results)

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