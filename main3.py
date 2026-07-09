import pandas as pd
import numpy as np
from backtester import BackTester

def process_data(data):
    """
    Process the input data and return a dataframe with all the necessary indicators and data for making signals.
    """
    # MACD Line: 12 EMA - 26 EMA
    ema_12 = data['close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    
    # Signal Line: 9 EMA of MACD
    data['SIGNAL'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    # ATR 14 for trailing stop
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['ATR'] = tr.rolling(14).mean()
    
    return data

def strat(data):
    """
    MACD Momentum Strategy with ATR Trailing Stop
    """
    data['trade_type'] = "HOLD" 
    data['signals'] = 0
    position = 0 
    trailing_stop = 0  
    trailing_stop_multiplier = 2.5

    for i in range(35, len(data)):
        macd = data.loc[i, 'MACD']
        signal_line = data.loc[i, 'SIGNAL']
        macd_prev = data.loc[i-1, 'MACD']
        signal_prev = data.loc[i-1, 'SIGNAL']
        close_price = data.loc[i, 'close']
        atr = data.loc[i, 'ATR']

        if pd.isna(macd) or pd.isna(signal_line) or pd.isna(atr):
            continue

        bullish_cross = (macd > signal_line) and (macd_prev <= signal_prev)
        bearish_cross = (macd < signal_line) and (macd_prev >= signal_prev)

        if position == 0:
            if bullish_cross:
                data.loc[i, 'signals'] = 1
                position = 1
                data.loc[i, 'trade_type'] = "LONG"
                trailing_stop = close_price - (atr * trailing_stop_multiplier)
            elif bearish_cross:
                data.loc[i, 'signals'] = -1
                position = -1
                data.loc[i, 'trade_type'] = "SHORT"
                trailing_stop = close_price + (atr * trailing_stop_multiplier)

        elif position == 1:
            if bearish_cross:
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

        elif position == -1:
            if bullish_cross:
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
    csv_file_path = "final_data3.csv" 
    result_data.to_csv(csv_file_path, index=False)

    bt = BackTester("BTC", signal_data_path="final_data3.csv", master_file_path="final_data3.csv", compound_flag=1)
    bt.get_trades(1000)

    # print trades and their PnL
    for trade in bt.trades: 
        print(trade)
        print(trade.pnl())

    # Print results
    stats = bt.get_statistics()
    print("--- MACD MOMENTUM STATS ---")
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

    # Generate the PnL graph
    # bt.make_pnl_graph()
    
if __name__ == "__main__":
    main()
