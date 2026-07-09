# SatoshiFlow: Algorithmic Trading Strategies for Bitcoin (BTC/USD)

**Author:** Swapnil Purohit (24B2507)  
**Project:** Summer of Quant Final Submission

## Overview
This repository contains the development, optimization, and backtesting of three quantitative trading strategies designed for Bitcoin (BTC/USD). The strategies were rigorously tested on daily historical data spanning from 2018 to 2022. 

Bitcoin is highly volatile and exhibits strong, protracted trends on daily timeframes. Recognizing this, the project focuses heavily on trend-following and momentum-breakout systems, incorporating dynamic risk management (via Average True Range) and momentum filtering (via the Relative Strength Index) to maximize risk-adjusted returns.

---

## Strategy 1: Optimized EMA Trend-Following (The Winner)
**File:** `main.py`

This strategy was built to capture Bitcoin's massive, prolonged macroeconomic trends while aggressively protecting capital during market crashes. 

### Logic & Hypothesis
*   **Trend Identification (The Entry):** We use a crossover of two Exponential Moving Averages (EMA). Through grid-search optimization (found in `optimizer.py`), we discovered that a **25-day (Fast) and 75-day (Slow) EMA combination** perfectly balances responsiveness with the ability to ignore short-term market noise. A LONG position triggers when the 25-day EMA crosses above the 75-day EMA. A SHORT position triggers when it crosses below.
*   **Momentum Filtering:** Moving average crossovers are notoriously prone to "whipsaws" (false signals in a sideways market). To combat this, we implemented a 14-day **Relative Strength Index (RSI)** filter. 
    *   We only enter a LONG trade if `RSI < 70` (ensuring we aren't buying the absolute top of an overextended pump).
    *   We only enter a SHORT trade if `RSI > 30` (ensuring we aren't shorting the absolute bottom of a crash).
*   **Dynamic Risk Management (The Exit):** Cryptocurrencies are too volatile for static stop-losses. Instead, we exit positions using a **2.5x Average True Range (ATR)** trailing stop. As the trade becomes profitable, the stop-loss moves up with the price, locking in profits while remaining loose enough to let the asset breathe.

---

## Strategy 2: Donchian Channel Breakout (Turtle Trading)
**File:** `main2.py`

This is a momentum-based breakout system inspired by the famous "Turtle Traders" of the 1980s, adapted for modern cryptocurrency markets.

### Logic & Hypothesis
*   **The Breakout (Entry):** The strategy initiates a LONG position if the daily closing price breaks above the **highest high of the last 20 days**. It initiates a SHORT position if the price breaks below the **lowest low of the last 20 days**.
*   **Momentum Filtering:** Just like the EMA strategy, we found that adding an RSI filter massively improved performance (jumping net profit from $3.5k to $5.3k). We require `RSI < 70` for longs and `RSI > 30` for shorts to avoid buying into exhausted momentum.
*   **Dynamic Exit:** Positions are closed either when the trend reverses (hitting the 10-day low for longs, or 10-day high for shorts) OR when it hits our standard 2.5x ATR trailing stop. 

---

## Strategy 3: MACD Momentum
**File:** `main3.py`

This strategy attempts to capture shorter-term momentum shifts using the classic Moving Average Convergence Divergence indicator.

### Logic & Hypothesis
*   **The Crossover (Entry):** Trades are triggered by the MACD line (the difference between the 12-day and 26-day EMA) crossing its 9-day Signal Line. A cross above triggers a LONG, a cross below triggers a SHORT.
*   **Trailing Stop (Exit):** Uses the same 2.5x ATR trailing stop to manage downside risk.
*   **Why RSI Failed Here:** Interestingly, while the RSI filter vastly improved the first two strategies, it destroyed the profitability of the MACD strategy. Because MACD is inherently a lagging indicator, by the time a crossover signaled a trade, the RSI was often already indicating overbought or oversold conditions. The RSI filter ended up blocking almost all the valid breakout trades. Consequently, the MACD strategy is run *without* the RSI filter.

---

## Key Performance Metrics

The strategies were tested with an initial capital of $1,000 using 1x leverage. 

| Metric | EMA Trend (25/75) | Donchian Breakout | MACD Momentum |
| :--- | :--- | :--- | :--- |
| **Sharpe Ratio** | **1.147** | 0.922 | 0.760 |
| **Net Profit** | **$5,597.58** | $5,334.30 | $3,237.76 |
| **Win Rate** | **50.00%** | 44.18% | 36.58% |
| **Total Trades** | 48 | **43** | 123 (Overtrading) |
| **Max Drawdown** | **24.71%** | 45.88% | 52.53% |

### Final Rankings & Conclusion
1. **🥇 1st Place - Optimized EMA Trend-Following:** This strategy is the clear winner. By utilizing an RSI filter to avoid late entries and an ATR stop to manage risk, it yielded the highest Sharpe Ratio (1.147), the highest net profit ($5,597.58), and incredibly, the lowest Maximum Drawdown (24.71%). 
2. **🥈 2nd Place - Donchian Channel Breakout:** This strategy performed exceptionally well as a breakout system. It yielded a massive net profit ($5,334.30) and an excellent Sharpe Ratio of 0.922. However, its drawdowns (45.88\%) were notably higher than the EMA strategy due to delayed exit signals during rapid price reversals.
3. **🥉 3rd Place - MACD Momentum:** The MACD strategy generated too many false signals (whipsaws) in sideways markets. This led to over-trading (123 total trades), a poor win rate (36.58\%), and high commission costs, placing it firmly in last place.

---

## File Structure & Usage

*   **`main.py`**: The 1st place EMA strategy.
*   **`main2.py`**: The 2nd place Donchian strategy.
*   **`main3.py`**: The 3rd place MACD strategy.
*   **`optimizer.py`**: A custom grid-search script written to iteratively test combinations of Fast/Slow EMAs and ATR multipliers to find the mathematical optimum.
*   **`backtester.py`**: The provided core backtesting engine that simulates the trading environment, accounts for fees, and calculates the final statistics.
*   **`report.tex`**: The LaTeX code for the final submitted PDF report.

### How to Run
To test a strategy, simply run the corresponding python file in your terminal. The script will process the historical CSV data, apply the strategy logic, generate a `final_data.csv` file, and automatically trigger the backtester to display the results.

```bash
python main.py
```
*(Requires `pandas` and `numpy` to be installed in your Python environment).*
