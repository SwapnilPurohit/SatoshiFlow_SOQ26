import pandas as pd
import numpy as np
from backtester import BackTester


def process_data(data):
    """
    Process the input data and return a dataframe with all the necessary indicators and data for making signalss.

    Parameters:
    data (pandas.DataFrame): The input data to be processed.

    Returns:
    pandas.DataFrame: The processed dataframe with all the necessary indicators and data.
    """
    # Generate the necessary indicators here without external libraries
    
    # EMA Fast and Slow
    data['EMA_FAST'] = data['close'].ewm(span=25, adjust=False).mean()
    data['EMA_SLOW'] = data['close'].ewm(span=75, adjust=False).mean()
    
    # RSI 14 (Wilder's Smoothing)
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    data['RSI_14'] = 100 - (100 / (1 + rs))
    
    # ATR 14
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['ATR'] = tr.rolling(14).mean()
    
    return data


def strat(data):
    """
    Create a strategy based on indicators or other factors.

    Parameters:
    - data: DataFrame
        The input data containing the necessary columns for strategy creation.

    Returns:
    - DataFrame
        The modified input data with an additional 'signals' column representing the strategy signals.
    """
    data['trade_type'] = "HOLD" 
    data['signals'] = 0
    position = 0 # Variable to keep track of the current position (0 = no position, 1 = long, -1 = short)
    trailing_stop = 0  
    trailing_stop_multiplier = 2.5

    # Start from index 75 to ensure EMA_SLOW and ATR are valid
    for i in range(75, len(data)):
        ema_20 = data.loc[i, 'EMA_FAST']
        ema_50 = data.loc[i, 'EMA_SLOW']
        ema_20_prev = data.loc[i-1, 'EMA_FAST']
        ema_50_prev = data.loc[i-1, 'EMA_SLOW']
        rsi = data.loc[i, 'RSI_14']
        close_price = data.loc[i, 'close']
        atr = data.loc[i, 'ATR']

        # Skip if indicators are NaN
        if pd.isna(ema_20) or pd.isna(ema_50) or pd.isna(rsi) or pd.isna(atr):
            continue

        # Determine if there's a crossover
        bullish_cross = (ema_20 > ema_50) and (ema_20_prev <= ema_50_prev)
        bearish_cross = (ema_20 < ema_50) and (ema_20_prev >= ema_50_prev)

        if position == 0:
            if bullish_cross and rsi < 70:
                data.loc[i, 'signals'] = 1
                position = 1
                data.loc[i, 'trade_type'] = "LONG"
                trailing_stop = close_price - (atr * trailing_stop_multiplier)
            elif bearish_cross and rsi > 30:
                data.loc[i, 'signals'] = -1
                position = -1
                data.loc[i, 'trade_type'] = "SHORT"
                trailing_stop = close_price + (atr * trailing_stop_multiplier)

        elif position == 1: # We already have a long position
            if bearish_cross and rsi > 30:
                data.loc[i, 'signals'] = -2
                position = -1
                trailing_stop = close_price + (atr * trailing_stop_multiplier)
                data.loc[i, 'trade_type'] = "REVERSE_LONG_TO_SHORT"
            else:
                if close_price < trailing_stop:
                    data.loc[i, 'signals'] = -1
                    position = 0
                    data.loc[i, 'trade_type'] = 'CLOSE'
                else:
                    trailing_stop = max(trailing_stop, close_price - (atr * trailing_stop_multiplier))

        elif position == -1: # We already have a short position
            if bullish_cross and rsi < 70:
                data.loc[i, 'signals'] = 2
                position = 1
                trailing_stop = close_price - (atr * trailing_stop_multiplier)
                data.loc[i, 'trade_type'] = "REVERSE_SHORT_TO_LONG"
            else:
                if close_price > trailing_stop:
                    data.loc[i, 'signals'] = 1
                    position = 0
                    data.loc[i, 'trade_type'] = 'CLOSE'
                else:
                    trailing_stop = min(trailing_stop, close_price + (atr * trailing_stop_multiplier))

    return data

def main():
    data = pd.read_csv("btc_18_22_1d.csv")
    processed_data = process_data(data) # process the data
    result_data = strat(processed_data) # Apply the strategy
    csv_file_path = "final_data.csv" 
    result_data.to_csv(csv_file_path, index=False)

    bt = BackTester("BTC", signal_data_path="final_data.csv", master_file_path="final_data.csv", compound_flag=1)
    bt.get_trades(1000)

    # print trades and their PnL
    for trade in bt.trades: 
        print(trade)
        print(trade.pnl())

    # Print results
    stats = bt.get_statistics()
    for key, val in stats.items():
        print(key, ":", val)


    #Check for lookahead bias
    print("Checking for lookahead bias...")
    lookahead_bias = False
    for i in range(len(result_data)):
        if result_data.loc[i, 'signals'] != 0:  # If there's a signal
            temp_data = data.iloc[:i+1].copy()  # Take data only up to that point
            temp_data = process_data(temp_data) # process the data
            temp_data = strat(temp_data) # Re-run strategy
            if temp_data.loc[i, 'signals'] != result_data.loc[i, 'signals']:
                print(f"Lookahead bias detected at index {i}")
                lookahead_bias = True

    if not lookahead_bias:
        print("No lookahead bias detected.")

    # Generate the trade graph
    bt.make_trade_graph()
    
if __name__ == "__main__":
    main()