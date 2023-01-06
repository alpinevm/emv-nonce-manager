import os
from os.path import join, dirname
import json
from typing import Union
import time

import redis
from web3 import Web3, HTTPProvider
from web3.types import Wei
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from eth_account.account import Account
from eth_account.datastructures import SignedTransaction
from dotenv import load_dotenv
load_dotenv(join(dirname(__file__), '..' , '.env'))

# Connect to the Redis queue
redis_client: redis.Redis = redis.from_url(os.environ["REDIS_URL"])
queue = 'ethereum_transaction_queue'

# Connect to the Ethereum blockchain
w3: Web3 = Web3(HTTPProvider(os.environ["RPC_URL"]))

def process_transaction(payload: dict) -> None: 
    try:
        w3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
        funding_address: str = Account.from_key(os.environ["FUNDING_KEY"]).address
        nonce: int = w3.eth.get_transaction_count(funding_address)
        print("Processing request, using nonce: ", nonce)
        gas_price: Union[Wei, None] = w3.eth.generate_gas_price()
        if(gas_price == None):
             raise Exception("Failed to get gas price")
        signed_transaction: SignedTransaction = w3.eth.account.sign_transaction(
            {
                "nonce": nonce,
                "gasPrice": int(int(gas_price)*1.5),
                "gas": 21000,
                "from": w3.eth.account.from_key(os.environ["FUNDING_KEY"]).address,
                "to": payload["address"],
                "value": w3.toWei(0.00001, "ether"),
                "chainId": w3.eth.chain_id
            },
            os.environ["FUNDING_KEY"],
        )
        w3.eth.wait_for_transaction_receipt(
            w3.eth.send_raw_transaction(
                signed_transaction.rawTransaction
            )
        ,timeout=600)
        # The nonce doesn't update immediately across the network, so wait until it does...
        while(True):
            if nonce + 1 == w3.eth.get_transaction_count(funding_address):
                break 
            time.sleep(1)
        redis_client.publish(payload["channel_id"], "success")
    except:
        redis_client.publish(payload["channel_id"], "failure")

# Continuously process transactions as they are added to the queue
while True:
  # Process serially (blocking)
  queue_item: tuple[bytes, bytes] = redis_client.blpop(queue)
  payload: dict = json.loads(queue_item[1].decode('utf-8'))
  process_transaction(payload)

