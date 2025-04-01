import pandas as pd
import numpy as np

def run_backtest(data, signals, initial_capital=100000.0, allow_shorting=False):
    """
    Runs a simple vectorized backtest, handling long and optional short positions.

    Args:
        data (pd.DataFrame): DataFrame with 'Adj Close' prices, indexed by date.
        signals (pd.DataFrame): DataFrame with 'signal' column (1=buy, -1=sell/short, 0=hold/flat).
                                Index must align with data.
        initial_capital (float): Starting capital for the backtest.
        allow_shorting (bool): Whether short positions are allowed.

    Returns:
        pd.DataFrame: Portfolio DataFrame containing equity curve and positions.
                      Returns None if inputs are invalid.
    """
    if data is None or signals is None or data.empty or signals.empty:
        # print("Error: Backtester received invalid data or signals.") # Reduced verbosity
        return None
    if 'Adj Close' not in data.columns:
        print("Error: Backtester requires 'Adj Close' column in data.")
        return None
    if 'signal' not in signals.columns:
        print("Error: Backtester requires 'signal' column in signals.")
        return None

    # Align data and signals strictly on index
    common_index = data.index.intersection(signals.index)
    if common_index.empty:
        print("Error: Data and Signal indices have no overlap.")
        return None
    data = data.loc[common_index]
    signals = signals.loc[common_index]

    # print("Starting backtest...") # Reduced verbosity
    portfolio = pd.DataFrame(index=data.index)
    portfolio['Adj Close'] = data['Adj Close']
    portfolio['signal'] = signals['signal'] # Signal for decision *today*
    portfolio['position'] = 0.0 # Position held *during* the day, decided based on *yesterday's* signal
    portfolio['market_return'] = portfolio['Adj Close'].pct_change().fillna(0.0)

    # --- Determine Positions based on previous day's signal ---
    # Shift signals by 1 day: Use yesterday's signal to determine today's position holding
    shifted_signal = portfolio['signal'].shift(1).fillna(0.0)

    # Apply position logic
    portfolio['position'] = shifted_signal.apply(lambda x: 1.0 if x > 0 else (-1.0 if x < 0 and allow_shorting else 0.0))

    # --- Calculate Strategy Returns ---
    # Strategy return for day 't' is the position held *during* day 't' times the market return *of* day 't'.
    # The position held during day 't' was determined by the signal generated at the end of day 't-1'.
    portfolio['strategy_return'] = portfolio['position'] * portfolio['market_return']
    portfolio['strategy_return'].fillna(0.0, inplace=True) # Fill NaN for the first day

    # --- Calculate Cumulative Returns and Equity Curve ---
    portfolio['cumulative_market'] = (1 + portfolio['market_return']).cumprod()
    portfolio['cumulative_strategy'] = (1 + portfolio['strategy_return']).cumprod()
    portfolio['equity_curve'] = initial_capital * portfolio['cumulative_strategy']

    # Remove initial rows where signals/positions might be NaN due to rolling windows/shifting
    first_valid_index = portfolio['strategy_return'].first_valid_index()
    if first_valid_index is not None:
         portfolio = portfolio.loc[first_valid_index:]
    else:
         print("Warning: No valid strategy returns generated.")
         return None # No valid data points after processing

    if portfolio.empty:
        # print("Warning: Portfolio became empty after removing initial NaNs.") # Reduced verbosity
        return None

    # print(f"Backtest completed. Final portfolio value: ${portfolio['equity_curve'].iloc[-1]:,.2f}") # Reduced verbosity
    return portfolio