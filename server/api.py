import requests
import os
from flask import Flask
import json
from web3.auto.infura import w3
from uniswap import Uniswap
from eth_abi import decode_single, decode_abi


app = Flask(__name__)

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

eth = "0x0000000000000000000000000000000000000000"
bat = "0x0D8775F648430679A709E98d2b0Cb6250d2887EF"
dai = "0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359"

contracts = json.load(open("contracts.json", "r"))


@app.route("/")
def main():
    return "hi"


def find_tokens(transaction, contract_abi, contract_address):
    return w3.eth.contract(contract_address, abi=ether_abi)


def get_token_balance(my_address, token_name, block="latest"):
    my_address = w3.toChecksumAddress(my_address)
    contract_abi = contracts["abi"][token_name]
    contract_address = w3.toChecksumAddress(contracts["address"][token_name])
    contract = w3.eth.contract(contract_address, abi=contract_abi)
    print(contract.functions.name().call())
    print(contract.functions.name().call())
    balance = contract.functions.balanceOf(my_address).call()
    # int r0 = contract.functions.price0CumulativeLast().call()
    # print(r0)
    print(balance)
    return


@app.route("/wallet/<wallet>")
def get_transactions(wallet):
    wallet = wallet.lower()
    uniswap_wrapper = Uniswap(web3=w3, private_key=None, address=wallet)
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock=0&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    transactions = response.json()["result"]
    for transaction in transactions:
        deposit = transaction["to"].lower() == wallet
        transaction["txCost"] = 0
        if transaction["from"].lower() == wallet.lower():
            transaction["txCost"] = float(
                w3.fromWei(
                    int(transaction["gasUsed"]) * int(transaction["gasPrice"]),
                    "ether",
                )
            )

        transaction["values"] = {
            "ETH": float(w3.fromWei(int(transaction["value"]), "ether"))
            * (1 if deposit else -1)
        }
        for key, address in contracts["address"].items():
            if transaction["from"].lower() == address.lower():
                transaction["fromName"] = key
            if transaction["to"].lower() == address.lower():
                transaction["toName"] = key
                contract_abi = contracts["abi"].get(key)
                if contract_abi:
                    contract_address = w3.toChecksumAddress(contracts["address"][key])
                    contract = w3.eth.contract(contract_address, abi=contract_abi)
                    if len(transaction["input"]) > 4:
                        input = contract.decode_function_input(transaction["input"])
                        transaction["input"] = str(input)
                        for func in contract.functions.__dir__():
                            if input[0].fn_name == func:
                                transaction["name"] = func
                                if func == "approve":
                                    print("approve")
                                if func == "swapExactTokensForETH":
                                    transaction["value"] = input[1]["amountOutMin"]
                                    transaction["values"]["ETH"] = float(
                                        w3.fromWei(input[1]["amountOutMin"], "ether")
                                    )
                                if func == "swapETHForExactTokens":
                                    print(input[1]["path"][-1].lower())
                                    for token, address in contracts["address"].items():
                                        if (
                                            input[1]["path"][-1].lower()
                                            == address.lower()
                                        ):
                                            print(token)
                                            print(input[1])
                                            print(
                                                w3.fromWei(
                                                    input[1]["amountOut"], "ether"
                                                )
                                            )
                                            transaction["values"][token] = (
                                                float(
                                                    w3.fromWei(
                                                        input[1]["amountOut"], "gwei"
                                                    )
                                                )
                                                if token == "USDT"
                                                else float(
                                                    w3.fromWei(
                                                        input[1]["amountOut"], "ether"
                                                    )
                                                )
                                            )
                                if func == "swapExactETHForTokens":
                                    for token, address in contracts["address"].items():
                                        if (
                                            input[1]["path"][-1].lower()
                                            == address.lower()
                                        ):
                                            transaction["values"][token] = float(
                                                w3.fromWei(
                                                    input[1]["amountOutMin"], "ether"
                                                )
                                            )

                                if func == "addLiquidityETH":
                                    # print(input[1])
                                    for token, address in contracts["address"].items():
                                        if input[1]["token"].lower() == address.lower():
                                            # print(input[1])
                                            # print(contracts["address"][f"ETH/{token}"])
                                            tokenContract = w3.eth.contract(
                                                w3.toChecksumAddress(
                                                    contracts["address"][f"ETH/{token}"]
                                                ),
                                                abi=contracts["abi"][f"ETH/{token}"],
                                            )
                                            transaction["values"][
                                                f"ETH/{token}"
                                            ] = float(
                                                w3.fromWei(
                                                    tokenContract.functions.balanceOf(
                                                        w3.toChecksumAddress(wallet)
                                                    ).call(),
                                                    "ether",
                                                )
                                            )
                                            transaction["values"][token] = (
                                                float(
                                                    w3.fromWei(
                                                        input[1]["amountTokenDesired"],
                                                        "ether",
                                                    )
                                                )
                                                * -1
                                            )
                                if func == "stakeWithPermit":
                                    print("stakeWithPermit")
                                if func == "deposit":
                                    print("deposit")
                                if func == "withdraw":
                                    print("withdraw")
                                if func == "removeLiquidityETHWithPermit":
                                    print("removeLiquidityETHWithPermit")

        # transaction["values"][key] = get_token_balance(wallet, key)
        # print(transaction["values"])

    return {"transactions": transactions}
