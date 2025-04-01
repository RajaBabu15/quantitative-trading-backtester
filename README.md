
# Quantitative Trading Strategy Backtester

A Python framework for backtesting multiple quantitative trading strategies across various parameter combinations using historical stock data. This tool helps in identifying potentially robust strategy configurations based on performance metrics.

## Features

*   Loads historical price data (CSV format, requires `Date` and `Adj Close`).
*   Includes strategy implementations for:
    *   Momentum Strategy
    *   Mean Reversion Strategy
    *   Simple Moving Average (SMA) Crossover Strategy
*   Performs a **parameter sweep**, running backtests for a Cartesian product of specified strategy parameters.
*   Supports both **long-only** and **long/short** backtesting (configurable per run).
*   Runs vectorized backtest simulations (Note: simplified logic, see Disclaimer).
*   Calculates key performance metrics for each run:
    *   Cumulative Return
    *   Compound Annual Growth Rate (CAGR)
    *   Annualized Volatility
    *   Annualized Sharpe Ratio
    *   Annualized Sortino Ratio
    *   Maximum Drawdown
    *   Calmar Ratio
    *   Estimated Total Trades
*   Outputs a summary of the **top-performing combinations** to the console.
*   Saves **detailed results** (parameters + metrics) for *all* combinations to a CSV file.
*   Generates and saves a **plot** of the equity curve for the single **best-performing strategy** (based on Sharpe Ratio).

## Project Structure

```
quantitative-trading-backtester/
|-- data/                     # Folder for historical data files
|   `-- sample_data.csv       # Example/Your data file (NEEDS 5+ YEARS DATA)
|-- src/                      # Source code module
|   |-- __init__.py
|   |-- backtester.py         # Core backtesting engine
|   |-- data_handler.py       # Loads and prepares data
|   |-- performance.py        # Calculates performance metrics
|   |-- plotting.py           # Generates equity curve plot
|   `-- strategy.py           # Contains strategy logic classes
|-- backtest_results/         # Output folder (created automatically)
|   |-- all_backtest_results.csv  # CSV containing results for all runs
|   `-- best_strategy_plot_*.png # Plot of the best performing run
|-- .gitignore                # Git ignore file
|-- main.py                   # Main script to configure and run the parameter sweep
|-- README.md                 # This file
`-- requirements.txt          # Python dependencies
```

## Setup

1.  **Clone the repository (or create the files manually):**
    ```bash
    git clone https://github.com/RajaBabu15/quantitative-trading-backtester.git
    cd quantitative-trading-backtester
    ```

2.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Prepare Data:**
    *   Download historical **daily** price data for a stock or ETF (e.g., SPY, QQQ from Yahoo Finance).
    *   Ensure the CSV file has at least a `Date` column (format `YYYY-MM-DD`, ideally as the first column) and an `Adj Close` column. Other columns (Open, High, Low, Close, Volume) are ignored by default but good practice to include.
    *   Save the file as `data/sample_data.csv` (or update the `DATA_FILEPATH` in `main.py`).
    *   **CRITICAL:** For meaningful parameter sweeps, ensure you have **sufficiently long historical data (e.g., 5-10+ years)** covering different market regimes. Short datasets can lead to misleading, overfitted results.

## Running the Parameter Sweep

1.  **Configure the Sweep:** Open `main.py` and modify the `param_grid` dictionary. This defines the search space for the backtester:
    *   Add/remove strategy types (`'momentum'`, `'mean_reversion'`, `'sma_crossover'`).
    *   Adjust the lists of parameter values to test for each strategy (e.g., different `momentum_window` values, `mean_reversion_entry_z` thresholds, `sma_long_window` lengths).
    *   Configure `allow_shorting`: `[False]` for long-only, `[True]` for short-only (less common), or `[False, True]` to test both.
    *   You can also adjust `DATA_FILEPATH`, `INITIAL_CAPITAL`, `RISK_FREE_RATE`, and `OUTPUT_DIR` near the top of `main.py`.

2.  **Execute:** Run the main script from the project's root directory:
    ```bash
    python main.py
    ```
    *Note: Depending on the size of your `param_grid` and data length, this may take some time to run.*

## Output

The script will:

1.  **Console Output:**
    *   Print status messages indicating data loading and the total number of combinations to test.
    *   Log the parameters being tested for each combination run.
    *   Print a brief result (Sharpe, CAGR, Max Drawdown) for each successful run.
    *   Display a formatted table showing the **Top 5 performing combinations** (sorted by Sharpe Ratio).
    *   Print the detailed parameters and metrics for the **single best run**.
    *   Report the total execution time.

2.  **Files Saved in `backtest_results/`:**
    *   `all_backtest_results.csv`: A CSV file containing one row for each parameter combination tested, including the parameters used and all calculated performance metrics. Useful for further analysis (e.g., in Excel or Pandas).
    *   `best_strategy_plot_*.png`: A PNG image file showing the equity curve of the single best performing strategy (highest Sharpe Ratio) plotted against the market buy-and-hold benchmark.

## Disclaimer

This is a simplified educational backtester framework. It serves as a starting point but **does not** account for many real-world factors, including:

*   **Transaction Costs:** Commissions, broker fees, exchange fees are not included.
*   **Slippage:** The difference between the expected trade price and the actual execution price is ignored.
*   **Taxes:** Capital gains and other taxes are not modeled.
*   **Market Impact:** Assumes trades do not affect the market price (unrealistic for large orders).
*   **Data Biases:** Assumes data is perfectly clean (survivorship bias, lookahead bias in data sources are not explicitly handled beyond basic signal shifting).
*   **Position Sizing & Risk Management:** Uses a fixed position state (fully invested long/short or flat) without sophisticated capital allocation or stop-loss mechanisms.
*   **Interest on Cash/Margin:** Does not model interest earned on cash balances or costs for borrowing on margin for short sales.

**Use this tool for educational purposes and initial strategy exploration only.** Results from this backtester may not accurately reflect real-world trading performance. Always perform further rigorous testing and consider real-world complexities before deploying any trading strategy. Past performance is not indicative of future results.
