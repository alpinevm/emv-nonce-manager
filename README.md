# Ethereum Transaction Nonce Manager
Simply and safely send `n` transactions from a single account without managing it's nonce.

## Testing
**Installation**
```bash
git clone https://github.com/alpinevm/evm-nonce-manager.git && cd evm-nonce-manager
python -m pip install -r -requirements.txt
```
**Setup**

create a `.env` at the root directory filled with the following info
```
REDIS_URL=your_redis_db_url
RPC_URL=an_ethereum_chain_rpc_url
FUNDING_KEY=your_funded_eth_private_key
```
**Test**

In seperate terminals:
```bash
python src/manager.py
```
```bash
python src/client.py
```
The `client` will send requests over a redis queue then wait for the response from the `manager` over a dedicated redis pub/sub channel for that request. 

## Todo

Currently the `manager` handles requests serially, one transaction per block. However by emitting multiple transactions with incrementally larger nonces there is no limit on the number of transactions from a single account that can fit in a block. This will obviously require more complex error handling as well (to auto resend transactions with higher nonces).

