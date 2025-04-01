import pandas as pd
import numpy as np

class Strategy:
    """Base class for trading strategies."""
    def __init__(self, data):
        self.data = data.copy()
        if self.data.empty:
            raise ValueError("Input data is empty.")
        self.signals = pd.DataFrame(index=self.data.index)
        self.signals['signal'] = 0.0 # Initialize signal column

    def generate_signals(self):
        """Generates trading signals (1 for buy, -1 for sell/short, 0 for hold/flat)."""
        raise NotImplementedError("Should implement generate_signals()")

    def get_signals(self):
        """Returns the generated signals DataFrame."""
        if 'signal' not in self.signals.columns:
             print("Warning: Signals have not been generated yet.")
             return pd.DataFrame(index=self.data.index) # Return empty df with index
        return self.signals

# --- Momentum Strategy ---
class MomentumStrategy(Strategy):
    def __init__(self, data, window=20):
        super().__init__(data)
        self.window = window
        if len(data) < window + 1: # Need window + 1 for pct_change
             raise ValueError(f"Data length ({len(data)}) is less than the required momentum window + 1 ({window + 1}).")

    def generate_signals(self):
        """Generates signals based on simple price momentum."""
        # Calculate momentum (percentage change over the window)
        # shift(1) ensures we use past data to decide today's signal
        momentum = self.data['Adj Close'].pct_change(self.window).shift(1)

        # Buy signal: Positive momentum
        self.signals.loc[momentum > 0, 'signal'] = 1.0
        # Sell/Short signal: Negative momentum
        self.signals.loc[momentum < 0, 'signal'] = -1.0
        # If momentum is NaN (at the start), signal remains 0

        print(f"Momentum signals generated (Window: {self.window}).")
        return self.signals

# --- Mean Reversion Strategy ---
class MeanReversionStrategy(Strategy):
    def __init__(self, data, window=20, entry_z=1.5, exit_z=0.5):
        super().__init__(data)
        self.window = window
        self.entry_z = entry_z
        self.exit_z = exit_z
        if len(data) < window:
             raise ValueError(f"Data length ({len(data)}) is less than the required mean reversion window ({window}).")

    def generate_signals(self):
        """Generates signals based on mean reversion logic."""
        # Calculate rolling mean and standard deviation
        rolling_mean = self.data['Adj Close'].rolling(window=self.window, min_periods=int(self.window*0.8)).mean() # Allow few NaNs at start
        rolling_std = self.data['Adj Close'].rolling(window=self.window, min_periods=int(self.window*0.8)).std()

        # Avoid division by zero or near-zero std dev
        rolling_std = rolling_std.replace(0, np.nan)

        # Calculate Z-score
        z_score = (self.data['Adj Close'] - rolling_mean) / rolling_std

        # Shift signals to avoid lookahead bias
        z_score_shifted = z_score.shift(1)

        # Entry Signal (Long): Price significantly below mean
        self.signals.loc[z_score_shifted < -self.entry_z, 'signal'] = 1.0

        # Entry Signal (Short): Price significantly above mean
        self.signals.loc[z_score_shifted > self.entry_z, 'signal'] = -1.0

        # Exit Signal Logic (Simplified): Exit when Z-score crosses the exit threshold
        # Note: A stateful backtester handles exits more accurately based on current position.
        # Here, we generate potential *triggers* for the backtester to use.
        # If z_score was below -entry_z and now is above -exit_z -> potential long exit
        # If z_score was above +entry_z and now is below +exit_z -> potential short exit
        # The backtester interprets signal=0 as "flatten position if held".
        # Conditions to potentially flatten a long position
        flatten_long_condition = (self.signals['signal'].shift(1) == 1.0) & (z_score_shifted > -self.exit_z)
        self.signals.loc[flatten_long_condition, 'signal'] = 0.0

        # Conditions to potentially flatten a short position
        flatten_short_condition = (self.signals['signal'].shift(1) == -1.0) & (z_score_shifted < self.exit_z)
        self.signals.loc[flatten_short_condition, 'signal'] = 0.0

        print(f"Mean Reversion signals generated (Window: {self.window}, Entry Z: {self.entry_z}, Exit Z: {self.exit_z}).")
        return self.signals[['signal']] # Return only the primary signal column

# --- SMA Crossover Strategy ---
class SMACrossoverStrategy(Strategy):
    def __init__(self, data, short_window=20, long_window=50):
        super().__init__(data)
        self.short_window = short_window
        self.long_window = long_window
        if short_window >= long_window:
            raise ValueError("Short window must be less than long window.")
        if len(data) < long_window:
             raise ValueError(f"Data length ({len(data)}) is less than the required long SMA window ({long_window}).")

    def generate_signals(self):
        """Generates signals based on SMA crossovers."""
        # Calculate short and long SMAs
        short_sma = self.data['Adj Close'].rolling(window=self.short_window, min_periods=self.short_window).mean()
        long_sma = self.data['Adj Close'].rolling(window=self.long_window, min_periods=self.long_window).mean()

        # Generate initial signals based on crossover logic
        # Shifted comparison to avoid lookahead bias (use yesterday's SMA values for today's signal)
        self.signals['short_sma'] = short_sma
        self.signals['long_sma'] = long_sma

        # Signal = 1 if short SMA crossed above long SMA yesterday
        self.signals.loc[(self.signals['short_sma'].shift(1) > self.signals['long_sma'].shift(1)) &
                           (self.signals['short_sma'].shift(2) <= self.signals['long_sma'].shift(2)), 'signal'] = 1.0

        # Signal = -1 if short SMA crossed below long SMA yesterday
        self.signals.loc[(self.signals['short_sma'].shift(1) < self.signals['long_sma'].shift(1)) &
                           (self.signals['short_sma'].shift(2) >= self.signals['long_sma'].shift(2)), 'signal'] = -1.0

        # Forward fill signals: Hold the position until the next crossover signal
        self.signals['signal'] = self.signals['signal'].ffill().fillna(0)

        # Correct signals: If yesterday's signal was buy(1), and today short<long, signal becomes 0 (sell)
        self.signals.loc[(self.signals['signal'].shift(1) == 1.0) & (self.signals['short_sma'] < self.signals['long_sma']), 'signal'] = 0.0
        # Correct signals: If yesterday's signal was sell(-1), and today short>long, signal becomes 0 (cover short)
        self.signals.loc[(self.signals['signal'].shift(1) == -1.0) & (self.signals['short_sma'] > self.signals['long_sma']), 'signal'] = 0.0


        print(f"SMA Crossover signals generated (Short: {self.short_window}, Long: {self.long_window}).")
        return self.signals[['signal']]