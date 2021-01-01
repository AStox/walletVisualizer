from celery import Celery
from app import app

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(bind=True)
def get_transactions(self, wallet, blockNumber):
    print("Request received...")
    price_info = PriceInfo.get_instance()
    contracts_info = Contracts.get_instance()
    price_info.prices = json.load(open("prices.json", "r"))
    wallet = w3.toChecksumAddress(wallet)
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock={blockNumber}&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    new_transactions = response.json()["result"]
    contracts_info.populate_contract_data(new_transactions, special_contracts)
    contracts = contracts_info.contracts

    

    for index, transaction in enumerate(new_transactions):
        message = f"processing transaction {transaction['hash']}"
        self.update_state(state='PROGRESS', meta={'current': index, 'total': len(new_transactions),'status': message})
        transaction["values"] = {}
        transaction["prices"] = {}
        transaction["txCost"] = 0
        transaction["to"] = w3.toChecksumAddress(transaction["to"])
        transaction["from"] = w3.toChecksumAddress(transaction["from"])
        deposit = transaction["to"] == wallet
        if transaction["from"] == wallet:
            transaction["txCost"] = float(
                w3.fromWei(
                    int(transaction["gasUsed"]) * int(transaction["gasPrice"]),
                    "ether",
                )
            )
            transaction["values"]["ETH"] = -transaction["txCost"]
        from_contract = contracts_info.get_contract(address=transaction["from"])
        to_contract = contracts_info.get_contract(address=transaction["to"])
        transaction["fromName"] = from_contract.symbol() if from_contract else ""
        transaction["toName"] = to_contract.symbol() if to_contract else ""
        contract_abi = to_contract.abi if to_contract else None
        if int(transaction["isError"]) == 0:
            transaction["values"] = {
                "ETH": int(transaction["value"])/pow(10, contracts["ETH"].decimals)
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
                        token1 = contracts["ETH"].address
                        token2 = input[1]["path"][0]
                        tokenContract = contracts_info.get_contract(token2)
                        poolContract = contracts_info.fetch_uniswap_pool_contract(token1, token2)
                        poolDecimals = poolContract.decimals
                        pool_symbols = [contracts_info.get_contract(poolContract.w3_contract.functions.token0().call()).symbol(),contracts_info.get_contract(poolContract.w3_contract.functions.token1().call()).symbol()]
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"]["ETH"] = poolContract.w3_contract.events.Swap().processLog(logs[-2])["args"][f"amount{pool_symbols.index('ETH')}Out"]/pow(10,contracts["ETH"].decimals)- transaction["txCost"]
                            transaction["values"][tokenContract.symbol()] = -poolContract.w3_contract.events.Swap().processLog(logs[-2])["args"][f"amount{pool_symbols.index(tokenContract.symbol())}In"]/pow(10, tokenContract.decimals)
                    if func == "swapETHForExactTokens":
                        address = input[1]["path"][-1]
                        token_contract = contracts_info.get_contract(address=address)
                        txHash = transaction["hash"]
                        time.sleep(0.1)
                        internalTx = requests.get(
                            f"https://api.etherscan.io/api?module=account&action=txlistinternal&txhash={txHash}&apikey={etherscan_api_key}"
                        ).json()["result"]
                        for tx in internalTx:
                            if tx["to"].lower() == wallet:
                                transaction["values"]["ETH"] += (
                                            int(tx["value"])/pow(10,contracts["ETH"].decimals)
                                    - transaction["txCost"]
                                )

                        transaction["values"][token_contract.symbol()] = (
                                input[1]["amountOut"]/pow(10,token_contract.decimals)
                        )
                    if func == "swapExactETHForTokens":
                        token1 = contracts["ETH"].address
                        token2 = input[1]["path"][-1].lower()
                        tokenContract = contracts_info.get_contract(token2)
                        poolContract = contracts_info.fetch_uniswap_pool_contract(token1, token2,)
                        poolDecimals = poolContract.decimals
                        txHash = transaction["hash"]
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"][tokenContract.symbol()] = poolContract.w3_contract.events.Swap().processLog(logs[-1])["args"]["amount0Out"]/pow(10, tokenContract.decimals)
                            transaction["values"]["ETH"] = (-int(transaction["value"])/pow(10, poolDecimals)- transaction["txCost"])

                    if func == "addLiquidityETH":
                        token_a = contracts["ETH"].address
                        token_b = input[1]["token"]
                        tokenContract = contracts_info.get_contract(token_b)
                        poolContract = contracts_info.fetch_uniswap_pool_contract(token_a, token_b)
                        poolDecimals = poolContract.decimals
                        pool_symbols = [contracts_info.get_contract(poolContract.w3_contract.functions.token0().call()).symbol(),contracts_info.get_contract(poolContract.w3_contract.functions.token1().call()).symbol()]
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"][poolContract.symbol()] = poolContract.w3_contract.events.Transfer().processLog(logs[-3])["args"]["value"]/pow(10,poolDecimals)
                            price_info.liquidity_positions[poolContract.symbol()] = {
                                "timestamp": int(transaction["timeStamp"]),
                                "token_bal": transaction["values"][poolContract.symbol()],
                            }
                            transaction["values"]["ETH"] = -poolContract.w3_contract.events.Mint().processLog(logs[-1])["args"][f"amount{pool_symbols.index('ETH')}"]/pow(10,contracts["ETH"].decimals)- transaction["txCost"]
                            if transaction["values"].get(tokenContract.symbol()) == None:
                                transaction["values"][tokenContract.symbol()] = 0
                            transaction["values"][tokenContract.symbol()] -= poolContract.w3_contract.events.Mint().processLog(logs[-1])["args"][f"amount{pool_symbols.index(tokenContract.symbol())}"]/pow(10,tokenContract.decimals)

                    if func == "removeLiquidityETHWithPermit":
                        token2 = input[1]["token"]
                        token1 = contracts["ETH"].address
                        tokenContract = contracts_info.get_contract(token2)
                        poolContract = contracts_info.fetch_uniswap_pool_contract(token1, token2)
                        poolDecimals = poolContract.decimals
                        pool_symbols = [contracts_info.get_contract(poolContract.w3_contract.functions.token0().call()).symbol(),contracts_info.get_contract(poolContract.w3_contract.functions.token1().call()).symbol()]
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"][poolContract.symbol()] = -(poolContract.w3_contract.events.Transfer().processLog(logs[1])["args"]["value"])/pow(10, poolDecimals)
                            transaction["values"]["ETH"] = (poolContract.w3_contract.events.Burn().processLog(logs[-3])["args"][f"amount{pool_symbols.index('ETH')}"])/pow(10,contracts["ETH"].decimals)- transaction["txCost"]
                        # if transaction["values"].get(tokenContract.symbol()) == None:
                        #     transaction["values"][tokenContract.symbol()] = 0
                        transaction["values"][tokenContract.symbol()] = poolContract.w3_contract.events.Burn().processLog(logs[-3])["args"][f"amount{pool_symbols.index(tokenContract.symbol())}"]/pow(10, tokenContract.decimals)
                    if func == "stakeWithPermit":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "deposit":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                        print(input[1])
                    if func == "withdraw":
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        for log in logs:
                            transaction_contract = contracts_info.get_contract(log["address"])
                            try:
                                transfer = transaction_contract.w3_contract.events.Transfer().processLog(log)
                                if w3.toChecksumAddress(transfer["args"]["to"]) == wallet:
                                    token_contract = contracts_info.get_contract(transfer["address"])
                                    transaction["values"][token_contract.symbol()] = transfer["args"]["value"]/pow(10, token_contract.decimals)
                            except exceptions.ABIEventFunctionNotFound:
                                pass
                        transaction["values"]["ETH"] = -transaction["txCost"]
                        
                    if func == "exit":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "transfer":
                        transaction["values"][to_contract.symbol()] = -(input[1]['wad'])/pow(10, poolDecimals)
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    print(func)

    new_transactions =  new_transactions
    last_block_number = new_transactions[-1]["blockNumber"]
    new_transactions = fill_out_dates(new_transactions)
    new_transactions = group_by_date(new_transactions)

    message = "fetching historical prices"
    self.update_state(state='PROGRESS', meta={'current': len(new_transactions)+1, 'total': len(new_transactions)+5,'status': message})
    price_info.prices = {**price_info.prices, **fetch_price_data(new_transactions)}

    message = "Compiling token balances"
    self.update_state(state='PROGRESS', meta={'current': len(new_transactions)+2, 'total': len(new_transactions)+5,'status': message})
    reduce(balance_calc, new_transactions, {})

    message = "Calculating staked liquidity returns"
    self.update_state(state='PROGRESS', meta={'current': len(new_transactions)+3, 'total': len(new_transactions)+5,'status': message})
    liquidity_returns = get_batched_returns(price_info.liquidity_position_timestamps)
    liquidity_returns_calculations(new_transactions, liquidity_returns)

    message = "Calculating percent changes"
    self.update_state(state='PROGRESS', meta={'current': len(new_transactions)+4, 'total': len(new_transactions)+5,'status': message})
    total_balance_calculations(new_transactions)
    percent_change_calculations(new_transactions)

    message = "Finished"
    self.update_state(state='PROGRESS', meta={'current': len(new_transactions)+5, 'total': len(new_transactions)+5,'status': message})
    addressData = {"transactions": new_transactions, "all_tokens": price_info.all_tokens, "last_block_number": last_block_number}
    return addressData