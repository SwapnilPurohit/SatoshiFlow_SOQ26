import pandas as pd
import numpy as np
from backtester import BackTester

def process_data(data, fast_ema=20, slow_ema=50):
    data['EMA_FAST'] = data['close'].ewm(span=fast_ema, adjust=False).mean()
    data['EMA_SLOW'] = data['close'].ewm(span=slow_ema, adjust=False).mean()
    
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    data['RSI_14'] = 100 - (100 / (1 + rs))
    
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['ATR'] = tr.rolling(14).mean()
    return data

def strat(data, atr_mult=2.5):
    data['trade_type'] = "HOLD" 
    data['signals'] = 0
    position = 0 
    trailing_stop = 0  
    trailing_stop_multiplier = atr_mult

    for i in range(50, len(data)):
        ema_fast = data.loc[i, 'EMA_FAST']
        ema_slow = data.loc[i, 'EMA_SLOW']
        ema_fast_prev = data.loc[i-1, 'EMA_FAST']
        ema_slow_prev = data.loc[i-1, 'EMA_SLOW']
        rsi = data.loc[i, 'RSI_14']
        close_price = data.loc[i, 'close']
        atr = data.loc[i, 'ATR']

        if pd.isna(ema_fast) or pd.isna(ema_slow) or pd.isna(rsi) or pd.isna(atr):
            continue

        bullish_cross = (ema_fast > ema_slow) and (ema_fast_prev <= ema_slow_prev)
        bearish_cross = (ema_fast < ema_slow) and (ema_fast_prev >= ema_slow_prev)

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

        elif position == 1:
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

        elif position == -1:
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
    import os
    import sys
    
    raw_data = pd.read_csv("btc_18_22_1d.csv")
    
    ema_pairs = [(10, 30), (15, 45), (20, 50), (25, 75)]
    atr_mults = [1.5, 2.0, 2.5, 3.0]
    
    best_sharpe = -999
    best_params = None
    
    for fast, slow in ema_pairs:
        for atr in atr_mults:
            data = raw_data.copy()
            processed_data = process_data(data, fast, slow)
            result_data = strat(processed_data, atr)
            result_data.to_csv("temp_opt.csv", index=False)
            
            # suppress prints
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            
            bt = BackTester("BTC", signal_data_path="temp_opt.csv", master_file_path="temp_opt.csv", compound_flag=1)
            bt.get_trades(1000)
            stats = bt.get_statistics()
            
            sys.stdout = old_stdout
            
            if stats is None: continue
            
            sharpe = stats.get('Sharpe Ratio', 0)
            if sharpe is not None and sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = (fast, slow, atr)
                
    print(f"Best Sharpe: {best_sharpe}")
    print(f"Best Params: EMA Fast={best_params[0]}, EMA Slow={best_params[1]}, ATR Mult={best_params[2]}")
    
    if os.path.exists("temp_opt.csv"):
        os.remove("temp_opt.csv")

if __name__ == "__main__":
    main()
