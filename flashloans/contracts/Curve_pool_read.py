from web3 import Web3
from decouple import config
import json
import requests
import time
import math
from Uniswap_pool_read import *

path = "CurveQueries"
CURVE_URL = config("CURVE_SUBGRAPH_URL")
CURVE_VOLUME_URL = config("CURVE_VOLUME_SUBGRAPH_URL")

# response = requests.post(CURVE_URL, json={"query": "{ pools(first: 10) { id } }"})
# data = response.json()
# print(data)

response = get_query(CURVE_URL, f"{path}/tokens.json", int(7))
data = response.json()
tokens = data["data"]["tokens"]
# for i, tok in enumerate(tokens, start=1):
#     print(i, tok["id"])

response2 = get_query(CURVE_URL, f"{path}/underlying_coins.json", int(80))
response2 = response2.json()
coins = response2["data"]["underlyingCoins"]
token_id_symbol_list = []

for i, c in enumerate(coins, start=1):
    # print(i, c["pool"])
    # print("---")
    # print(i, c["token"]["id"], c["token"]["symbol"], c["token"]["name"])
    token_id_symbol_list.append([c["token"]["id"], c["token"]["symbol"]])

i = 0
for ids, sym in token_id_symbol_list:
    res = get_query(CURVE_VOLUME_URL, f"{path}/snapshotstokens.json", ids)
    res = res.json()
    if res["data"]["tokenSnapshots"]:
        print(f"{i} price for {sym}", res["data"]["tokenSnapshots"][0]["price"])
        print(f"---id: {ids}")
        i += 1

    # print("price", res["data"]["tokenSnapshots"][0]["price"])
