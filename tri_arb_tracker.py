#!/usr/bin/env python3
"""
TriArbTracker — поиск треугольных арбитражных возможностей на UniswapV2‑совместимых DEX.
"""

import os
import time
from itertools import combinations, permutations
from decimal import Decimal, getcontext

from web3 import Web3

# более точные расчёты
getcontext().prec = 28

# Загрузка настроек
RPC_URL        = os.getenv("ETH_RPC_URL")
FACTORY_ADDR   = os.getenv("FACTORY_ADDRESS")       # адрес UniswapV2Factory
ROUTER_ADDR    = os.getenv("ROUTER_ADDRESS")        # адрес UniswapV2Router02
TOKEN_LIST     = os.getenv("TOKEN_LIST", "")        # comma‑sep список адресов токенов
MIN_PROFIT_USD = Decimal(os.getenv("MIN_PROFIT_USD", "10"))  # минимальная прибыль в USD
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL", "600"))      # сек

if not all([RPC_URL, FACTORY_ADDR, ROUTER_ADDR, TOKEN_LIST]):
    print("❗ Задайте ETH_RPC_URL, FACTORY_ADDRESS, ROUTER_ADDRESS и TOKEN_LIST")
    exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print("❗ Не удалось подключиться к RPC‑узлу")
    exit(1)

FACTORY_ABI = [{
    "constant":True,"inputs":[],"name":"allPairsLength","outputs":[{"type":"uint256"}],"type":"function"
},{
    "constant":True,"inputs":[{"name":"","type":"uint256"}],"name":"allPairs","outputs":[{"name":"","type":"address"}],"type":"function"
}]

PAIR_ABI = [{
    "constant":True,"inputs":[],"name":"getReserves","outputs":[
        {"type":"uint112","name":"_reserve0"},
        {"type":"uint112","name":"_reserve1"},
        {"type":"uint32","name":"_blockTimestampLast"}],"type":"function"
},{
    "constant":True,"inputs":[],"name":"token0","outputs":[{"type":"address"}],"type":"function"
},{
    "constant":True,"inputs":[],"name":"token1","outputs":[{"type":"address"}],"type":"function"
}]

ROUTER_ABI = [{
    "name":"getAmountsOut","outputs":[{"type":"uint256[]","name":""}],
    "inputs":[{"type":"uint256","name":"amountIn"},{"type":"address[]","name":"path"}],
    "constant":True,"stateMutability":"view","type":"function"
}]

factory = w3.eth.contract(address=FACTORY_ADDR, abi=FACTORY_ABI)
router  = w3.eth.contract(address=ROUTER_ADDR,  abi=ROUTER_ABI)

# Собираем токены
TOKENS = [w3.to_checksum_address(t.strip()) for t in TOKEN_LIST.split(",")]
print(f"🔍 TriArbTracker: проверяем {len(TOKENS)} токенов ({len(TOKENS)*(len(TOKENS)-1)*(len(TOKENS)-2)/6:.0f} треугольников)")

def find_triangles(tokens):
    # все уникальные комбинации по 3 токена
    return combinations(tokens, 3)

def simulate_triangle(tri, amount_in_wei):
    best = None
    # для каждой перестановки пути A→B→C→A
    for path in permutations(tri, 3):
        # добавим возвращение к первому
        full_path = list(path) + [path[0]]
        try:
            amounts = router.functions.getAmountsOut(amount_in_wei, full_path).call()
        except Exception:
            continue
        profit_wei = amounts[-1] - amount_in_wei
        if profit_wei > 0:
            if best is None or profit_wei > best[1]:
                best = (full_path, profit_wei)
    return best

def main():
    # возьмём за вход 1 токен первого списка в базовой единице (например, 1e18)
    sample_amount = 10**18
    while True:
        for tri in find_triangles(TOKENS):
            res = simulate_triangle(tri, sample_amount)
            if res:
                path, profit = res
                profit_eth = Decimal(profit) / Decimal(10**18)
                # грубая конвертация через ETH-USD oracle не включена, просто ETH-прибыль
                if profit_eth * Decimal(2000) >= MIN_PROFIT_USD:
                    print(f"💰 Арбитраж: {'→'.join([t[:8] for t in path])} | прибыль ≈ {profit_eth:.6f} ETH")
        print(f"Ждём {POLL_INTERVAL}s...\n")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
