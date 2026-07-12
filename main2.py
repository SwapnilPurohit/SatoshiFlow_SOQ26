import pandas as pd
import numpy as np
from backtester import BackTester

def process_data(data):
    """
    Process the input data and return a dataframe with all the necessary indicators and data for making signals.
    """
    # 20-Day High/Low (shifted by 1 to avoid lookahead bias)
    data['HIGH_20'] = data['high'].rolling(window=20).max().shift(1)
    data['LOW_20'] = data['low'].rolling(window=20).min().shift(1)
    
    # 10-Day High/Low (shifted by 1 to avoid lookahead bias)
    data['HIGH_10'] = data['high'].rolling(window=10).max().shift(1)
    data['LOW_10'] = data['low'].rolling(window=10).min().shift(1)
    
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
    high_close = np.abs(data['high'] - data['close'].shift(1))
    low_close = np.abs(data['low'] - data['close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['ATR'] = tr.rolling(14).mean()
    
    return data

def strat(data):
    """
    Donchian Channel Breakout Strategy (Turtle Trading)
    """
    data['trade_type'] = "HOLD" 
    data['signals'] = 0
    position = 0 
    trailing_stop = 0  
    trailing_stop_multiplier = 2.5

    for i in range(21, len(data)):
        high_20 = data.loc[i, 'HIGH_20']
        low_20 = data.loc[i, 'LOW_20']
        high_10 = data.loc[i, 'HIGH_10']
        low_10 = data.loc[i, 'LOW_10']
        rsi = data.loc[i, 'RSI_14']
        close_price = data.loc[i, 'close']
        atr = data.loc[i, 'ATR']

        if pd.isna(high_20) or pd.isna(atr) or pd.isna(rsi):
            continue

        if position == 0:
            if close_price > high_20 and rsi < 70:
                data.loc[i, 'signals'] = 1
                position = 1
                data.loc[i, 'trade_type'] = "LONG"
                trailing_stop = close_price - (atr * trailing_stop_multiplier)
            elif close_price < low_20 and rsi > 30:
                data.loc[i, 'signals'] = -1
                position = -1
                data.loc[i, 'trade_type'] = "SHORT"
                trailing_stop = close_price + (atr * trailing_stop_multiplier)

        elif position == 1:
            if close_price < low_20 and rsi > 30:
                data.loc[i, 'signals'] = -2
                position = -1
                data.loc[i, 'trade_type'] = "REVERSE_LONG_TO_SHORT"
                trailing_stop = close_price + (atr * trailing_stop_multiplier)
            elif close_price < low_10 or close_price < trailing_stop:
                data.loc[i, 'signals'] = -1
                position = 0
                data.loc[i, 'trade_type'] = 'CLOSE'
            else:
                trailing_stop = max(trailing_stop, close_price - (atr * trailing_stop_multiplier))

        elif position == -1:
            if close_price > high_20 and rsi < 70:
                data.loc[i, 'signals'] = 2
                position = 1
                data.loc[i, 'trade_type'] = "REVERSE_SHORT_TO_LONG"
                trailing_stop = close_price - (atr * trailing_stop_multiplier)
            elif close_price > high_10 or close_price > trailing_stop:
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
    csv_file_path = "final_data2.csv" 
    result_data.to_csv(csv_file_path, index=False)

    bt = BackTester("BTC", signal_data_path="final_data2.csv", master_file_path="final_data2.csv", compound_flag=1)
    bt.get_trades(1000)

    # Print results
    stats = bt.get_statistics()
    print("--- DONCHIAN CHANNEL STATS ---")
    if stats:
        for key, val in stats.items():
            print(key, ":", val)

    #Check for lookahead bias
    print("Checking for lookahead bias...")
    lookahead_bias = False
    for i in range(len(result_data)):
        if result_data.loc[i, 'signals'] != 0:
            temp_data = data.iloc[:i+1].copy()
            temp_data = process_data(temp_data)
            temp_data = strat(temp_data)
            if temp_data.loc[i, 'signals'] != result_data.loc[i, 'signals']:
                print(f"Lookahead bias detected at index {i}")
                lookahead_bias = True

    if not lookahead_bias:
        print("No lookahead bias detected.")

    # Generate the trade graph
    bt.make_trade_graph()
    
if __name__ == "__main__":
    main()
