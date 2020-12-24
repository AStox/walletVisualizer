import requests
import os
import time
import json
import functools
from flask import Flask, request
from functools import reduce
from web3.auto.infura import w3

from liquidity_pool_returns import get_batched_returns
from price_fetcher import fetch_price_data
from contracts import Contracts, fetch_abi, fetch_uniswap_pool_contract
from prices import PriceInfo, percent_change_calculations, liquidity_returns_calculations, total_balance_calculations, balance_calc
from transactions import fill_out_dates, group_by_date

app = Flask(__name__)

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

old_contracts = json.load(open("contracts.json", "r"))

errors = []

@app.route("/")
def main():
    return "hi"

@app.route("/wallet/<wallet>")
def get_transactions(wallet):
    print("Request received...")
    price_info = PriceInfo.getInstance()
    contracts_info = Contracts.getInstance()
    price_info.prices = json.load(open("prices.json", "r"))
    wallet = wallet.lower()
    blockNumber = request.args.get("blockNumber")
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock={blockNumber}&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    new_transactions = response.json()["result"]
    contracts_info.populate_contract_data(new_transactions, old_contracts)
    contracts = contracts_info.contracts

    print([key for key, value in contracts.items()])

    for transaction in new_transactions:
        transaction["values"] = {}
        transaction["prices"] = {}
        transaction["txCost"] = 0
        deposit = transaction["to"].lower() == wallet
        if transaction["from"].lower() == wallet.lower():
            transaction["txCost"] = float(
                w3.fromWei(
                    int(transaction["gasUsed"]) * int(transaction["gasPrice"]),
                    "ether",
                )
            )
            transaction["values"]["ETH"] = -transaction["txCost"]
        from_contract = contracts_info.get_contract(address=transaction["from"])
        to_contract = contracts_info.get_contract(address=transaction["to"])
        transaction["fromName"] = from_contract.symbol if from_contract else ""
        transaction["toName"] = to_contract.symbol if to_contract else ""
        contract_abi = to_contract.abi if to_contract else None
        if int(transaction["isError"]) == 0:
            transaction["values"] = {
                "ETH": int(transaction["value"])/pow(10, contracts["WETH"].decimals)
                * (1 if deposit else -1)
            }
            if contract_abi:
                contract_address = w3.toChecksumAddress(to_contract.address)
                contract = w3.eth.contract(contract_address, abi=contract_abi)
                if len(transaction["input"]) > 4:
                    input = contract.decode_function_input(transaction["input"])
                    transaction["input"] = str(input)
                    func = input[0].fn_name
                    transaction["name"] = func
                    if func == "approve":
                        transaction["values"]["ETH"] -= transaction["txCost"]
                    if func == "swapExactTokensForETH":
                        token1 = contracts["WETH"].address
                        token2 = input[1]["path"][0]
                        contracts_info.get_contract(token2)
                        token_abi = fetch_abi(token2)
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(token2),
                            abi=token_abi
                        )
                        symbol = tokenContract.functions.symbol().call()
                        poolContract = fetch_uniswap_pool_contract(token1, token2, contracts, name=f"ETH/{symbol}")
                        poolDecimals = poolContract.functions.decimals().call()
                        # TODO: DONT USE BALANCEOF HERE IT WON"T SCALE
                        transaction["values"][f"ETH/{symbol}"] = float(
                            tokenContract.functions.balanceOf(
                                w3.toChecksumAddress(wallet)
                            ).call()/pow(10, poolDecimals)
                        )
                        pool = f"WETH/{symbol}"
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"]["ETH"] = poolContract.events.Swap().processLog(logs[-2])["args"]["amount1Out"]/pow(10,contracts["WETH"]["decimals"])- transaction["txCost"]
                        if transaction["values"].get(symbol) == None:
                            transaction["values"][symbol] = 0
                        transaction["values"][symbol] = -poolContract.events.Swap().processLog(logs[-2])["args"]["amount0In"]/pow(10, poolDecimals)
                    if func == "swapETHForExactTokens":
                        address = input[1]["path"][-1].lower()
                        key = contracts_info.get_contract(address=input[1]["path"][-1].lower()).symbol
                        txHash = transaction["hash"]
                        time.sleep(0.1)
                        internalTx = requests.get(
                            f"https://api.etherscan.io/api?module=account&action=txlistinternal&txhash={txHash}&apikey={etherscan_api_key}"
                        ).json()["result"]
                        for tx in internalTx:
                            if tx["to"].lower() == wallet:
                                transaction["values"]["ETH"] += (
                                            int(tx["value"])/pow(10,contracts["WETH"]["decimals"])
                                    - transaction["txCost"]
                                )

                        transaction["values"][key] = (
                                input[1]["amountOut"]/pow(10,contracts[key]["decimals"])
                        )
                    if func == "swapExactETHForTokens":
                        token1 = contracts["WETH"]["address"]
                        token2 = input[1]["path"][-1].lower()
                        poolContract = fetch_uniswap_pool_contract(token1, token2, contracts)
                        poolDecimals = poolContract.functions.decimals().call()
                        txHash = transaction["hash"]
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"][token] = poolContract.events.Swap().processLog(logs[-1])["args"]["amount0Out"]/pow(10, poolDecimals)
                            transaction["values"]["ETH"] = (-int(transaction["value"])/pow(10, poolDecimals)- transaction["txCost"])

                    if func == "addLiquidityETH":
                        token1 = contracts["WETH"]["address"]
                        token2 = input[1]["token"]
                        poolContract = fetch_uniswap_pool_contract(token1, token2, contracts)
                        poolDecimals = poolContract.functions.decimals().call()
                        token_abi = fetch_abi(token2)
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(token2),
                            abi=token_abi
                        )
                        token = tokenContract.functions.symbol().call()
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            eth_pool = f"ETH/{token}"
                            if transaction["values"].get(eth_pool) == None:
                                transaction["values"][eth_pool] = 0
                            transaction["values"][eth_pool] = poolContract.events.Transfer().processLog(logs[-3])["args"]["value"]/pow(10,poolDecimals)
                            price_info.liquidity_positions[eth_pool] = {
                                "timestamp": int(transaction["timeStamp"]),
                                "token_bal": transaction["values"][eth_pool],
                            }
                            transaction["values"]["ETH"] = -poolContract.events.Mint().processLog(logs[-1])["args"]["amount1"]/pow(10,contracts["WETH"]["decimals"])- transaction["txCost"]
                            if transaction["values"].get(token) == None:
                                transaction["values"][token] = 0
                            transaction["values"][token] -= poolContract.events.Mint().processLog(logs[-1])["args"]["amount0"]/pow(10,contracts[token]["decimals"])

                    if func == "stakeWithPermit":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "deposit":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "withdraw":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "removeLiquidityETHWithPermit":
                        token1 = contracts["WETH"]["address"]
                        token2 = input[1]["token"]
                        poolContract = fetch_uniswap_pool_contract(token1, token2, contracts)
                        poolDecimals = poolContract.functions.decimals().call()
                        token_abi = fetch_abi(token2)
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(token2),
                            abi=token_abi
                        )
                        token = tokenContract.functions.symbol().call()
                        # TODO: DONT USE BALANCEOF HERE IT WON"T SCALE
                        transaction["values"][f"ETH/{token}"] = poolContract.functions.balanceOf(w3.toChecksumAddress(wallet)).call()/pow(10, poolDecimals)
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"]["ETH"] = (poolContract.events.Burn().processLog(logs[-3])["args"]["amount1"])/pow(10,contracts["WETH"]["decimals"])- transaction["txCost"]
                        if transaction["values"].get(token) == None:
                            transaction["values"][token] = 0
                        transaction["values"][token] = poolContract.events.Burn().processLog(logs[-3])["args"]["amount0"]/pow(10, poolDecimals)
                    if func == "exit":
                        transaction["values"]["ETH"] = -transaction["txCost"]

    new_transactions =  new_transactions
    last_block_number = new_transactions[-1]["blockNumber"]
    new_transactions = fill_out_dates(new_transactions)

    new_transactions = group_by_date(new_transactions)
    price_info.prices = {**price_info.prices, **fetch_price_data(new_transactions, contracts)}

    reduce(functools.partial(balance_calc, contracts=contracts), new_transactions, {})
    liquidity_returns = get_batched_returns(price_info.liquidity_position_timestamps)
    liquidity_returns_calculations(new_transactions, liquidity_returns)
    total_balance_calculations(new_transactions)
    percent_change_calculations(new_transactions)
    addressData = {"transactions": new_transactions, "all_tokens": price_info.all_tokens, "last_block_number": last_block_number}
    return addressData

