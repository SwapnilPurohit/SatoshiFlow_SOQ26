# SatoshiFlow: Bitcoin Algorithmic Trading

This repository contains the final project for the Summer of Quant. It features three algorithmic trading strategies tested on historical Bitcoin (BTC/USD) data from 2018-2022.

## Strategies Included
1. **Optimized EMA Trend-Following (`main.py`)**: Our primary, winning strategy. It uses a 25/75-day Exponential Moving Average crossover, filtered by RSI, and managed by a 2.5x ATR dynamic trailing stop. 
2. **Donchian Channel Breakout (`main2.py`)**: A momentum breakout strategy (Turtle Trading) that buys new 20-day highs and incorporates an RSI filter to avoid overbought markets.
3. **MACD Momentum (`main3.py`)**: A short-term trend strategy using the classic Moving Average Convergence Divergence indicator.

## Setup & Execution
The project uses a custom backtesting framework (`backtester.py`) to simulate trades, calculate PnL, and generate performance metrics like the Sharpe Ratio and Maximum Drawdown.

To run any of the strategies:
```bash
python main.py
```
