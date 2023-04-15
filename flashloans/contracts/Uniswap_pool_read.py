from web3 import Web3
from decouple import config
import json
import requests
import time
import math

UNISWAP_V3_FACRTORY_ADDRESS = config("UNISWAP_V3_FACTORY_ADDRESS")
UNISWAP_V3_FACTORY_ABI = json.loads(config("UNISWAP_V3_FACTORY_ABI"))

UNISWAP_V3_ROUTER_ADDRESS = config("UNISWAP_V3_ROUTER_ADDRESS")
UNISWAP_V3_ROUTER_ABI = json.loads(config("UNISWAP_V3_ROUTER_ABI"))

UNISWAP_V3_MULTICALL2 = json.loads(config("UNISWAP_V3_MULTICALL2"))
UNISWAP_V3_MULTICALL2_ADDRESS = config("UNISWAP_V3_MULTICALL2_ADDRESS")

UNISWAP_V3_SUBGRAPH_URL = config("UNISWAP_V3_SUBGRAPH_URL")

infura_url = config("MAINNET_PROVIDER_URL")
w3 = Web3(Web3.HTTPProvider(infura_url))

# contracts######################
uniswap_factory = w3.eth.contract(
    address=UNISWAP_V3_FACRTORY_ADDRESS, abi=UNISWAP_V3_FACTORY_ABI
)
router_contract = w3.eth.contract(
    address=UNISWAP_V3_ROUTER_ADDRESS, abi=UNISWAP_V3_ROUTER_ABI
)

multicall_contract = w3.eth.contract(
    address=UNISWAP_V3_MULTICALL2_ADDRESS, abi=UNISWAP_V3_MULTICALL2
)
##################################


def load_query(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def modify_query(file_path, token_address, new_token_address):
    query = load_query(file_path)
    query_template = query["query"]
    modified_query = query_template.replace(f"{token_address}", f"{new_token_address}")
    query["query"] = modified_query
    with open(file_path, "w") as f:
        json.dump(query, f)

    return query


def calculate_token_amounts(pool):
    liquidity = float(pool["liquidity"])
    tick = int(pool["tick"])
    tick_spacing = 60  # This can be 10, 60, or 200 depending on the pool's feeTier (0.05%, 0.3%, or 1% respectively)
    token0_decimals = int(pool["token0"]["decimals"])
    token1_decimals = int(pool["token1"]["decimals"])

    # Calculate token amounts
    lower_tick = math.floor(tick / tick_spacing) * tick_spacing
    upper_tick = lower_tick + tick_spacing

    sqrt_ratio_lower = math.sqrt(1.0001**lower_tick)
    sqrt_ratio_upper = math.sqrt(1.0001**upper_tick)

    token0_amount_wei = (
        liquidity * (sqrt_ratio_upper - sqrt_ratio_lower)
    ) / sqrt_ratio_lower
    token1_amount_wei = liquidity * (1 / sqrt_ratio_lower - 1 / sqrt_ratio_upper)

    # Convert token amounts to standard units
    token0_amount = token0_amount_wei / (10**token0_decimals)
    token1_amount = token1_amount_wei / (10**token1_decimals)

    return token0_amount, token1_amount


def pools_info(pool_id):
    query = load_query("UniswapQueries/pools_info_query.json")
    query = query["query"]

    variables = {"poolID": pool_id}

    response = requests.post(
        UNISWAP_V3_SUBGRAPH_URL,
        json={"query": query, "variables": variables},
    )

    data = response.json()

    if "errors" in data:
        print("Error fetching pool information:")
        print(data["errors"])
    else:
        pool = data["data"]["pool"]
        print("eccallà", pool)
        # print(pool)
        # token0_amount, token1_amount = calculate_token_amounts(pool)

        token0_amount = pool["totalValueLockedToken0"]
        token1_amount = pool["totalValueLockedToken1"]
        print(
            f"Token0 {data['data']['pool']['token0']['symbol']} amount: {token0_amount}"
        )
        print(
            f"Token1 {data['data']['pool']['token1']['symbol']}  amount: {token1_amount}"
        )


def pool_creation():
    event_filter = uniswap_factory.events.PoolCreated.createFilter(fromBlock="latest")
    while True:
        for event in event_filter.get_new_entries():
            print("event", event)
            print("event", event["args"]["pool"])
            pools_info(event["args"]["pool"])
        time.sleep(4)


def get_query(file_path, variables):
    query = load_query(file_path)
    var = list(query["variables"].keys())[0]
    query = query["query"]
    variables = {f"{var}": f"{variables}"}
    response = requests.post(
        UNISWAP_V3_SUBGRAPH_URL, json={"query": query, "variables": variables}
    )

    return response


def main():
    WETH_ADDR = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"

    response = get_query("UniswapQueries/tokenpools.json", WETH_ADDR)
    data = json.loads(response.text)

    if response.status_code == 200:
        pools = data["data"]["pools"]
        print("polli", pools[5])
        if pools is not None:
            print("First 10 pool IDs:")
            for i, pool in enumerate(pools, start=1):
                print("{}. {}".format(i, pool["token1"]["name"]))
                print(" pool", pool["id"])
                pools_info(pool["id"])
    else:
        print(f"Error: {data['errors'][0]['message']}")


if __name__ == "__main__":
    main()
    # eth "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
