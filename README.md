# TriArbTracker

**TriArbTracker** — утилита для поиска треугольных арбитражных возможностей на UniswapV2‑совместимых DEX.

## Концепция

Треугольный арбитраж состоит в последовательных обменах A→B→C→A. Если в результате вы получаете больше исходного объёма — возникает прибыль.

TriArbTracker:
1. Берёт список токенов (`TOKEN_LIST`).
2. Перебирает все комбинации по 3 токена.
3. Симулирует все пути через `getAmountsOut`.
4. Выводит те, где `out > in` и прибыль в ETH×2000 USD ≥ `MIN_PROFIT_USD`.

## Установка

```bash
git clone https://github.com/<ваш-профиль>/TriArbTracker.git
cd TriArbTracker
pip install -r requirements.txt
