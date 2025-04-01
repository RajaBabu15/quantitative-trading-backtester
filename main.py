import pandas as pd
import itertools
import os
import time

from src.data_handler import load_data
from src.strategy import MomentumStrategy, MeanReversionStrategy, SMACrossoverStrategy # Import strategies
from src.backtester import run_backtest
from src.performance import calculate_performance_metrics
from src.plotting import plot_equity_curve
import numpy as np

# --- Configuration ---
DATA_FILEPATH = 'data/sample_data.csv' # MAKE SURE THIS HAS 5+ YEARS OF DATA
OUTPUT_DIR = 'backtest_results' # Folder to save results
INITIAL_CAPITAL = 100000.0
RISK_FREE_RATE = 0.02 # Example annual risk-free rate (e.g., 2%)

# --- Parameter Grid ---
param_grid = {
    'strategy_type': ['momentum', 'mean_reversion', 'sma_crossover'],
    'allow_shorting': [False, True],
    # Momentum Params
    'momentum_window': [20, 40, 60],
    # Mean Reversion Params
    'mean_reversion_window': [20, 40],
    'mean_reversion_entry_z': [1.0, 1.5, 2.0],
    'mean_reversion_exit_z': [0.0, 0.5],
    # SMA Crossover Params
    'sma_short_window': [15, 20],
    'sma_long_window': [40, 50, 60]
}

# --- Helper Function to Generate Combinations ---
def generate_parameter_combinations(grid):
    # Create lists of dictionaries, one for each strategy type
    combinations = []

    # Momentum
    mom_keys = ['strategy_type', 'allow_shorting', 'momentum_window']
    mom_grid = {k: grid[k] for k in mom_keys if k in grid}
    mom_grid['strategy_type'] = ['momentum'] # Ensure type is correct
    mom_values = [dict(zip(mom_grid.keys(), v)) for v in itertools.product(*mom_grid.values())]
    combinations.extend(mom_values)

    # Mean Reversion
    mr_keys = ['strategy_type', 'allow_shorting', 'mean_reversion_window', 'mean_reversion_entry_z', 'mean_reversion_exit_z']
    mr_grid = {k: grid[k] for k in mr_keys if k in grid}
    mr_grid['strategy_type'] = ['mean_reversion']
    mr_values = [dict(zip(mr_grid.keys(), v)) for v in itertools.product(*mr_grid.values())]
    combinations.extend(mr_values)

    # SMA Crossover
    sma_keys = ['strategy_type', 'allow_shorting', 'sma_short_window', 'sma_long_window']
    sma_grid = {k: grid[k] for k in sma_keys if k in grid}
    sma_grid['strategy_type'] = ['sma_crossover']
    sma_values = [dict(zip(sma_grid.keys(), v)) for v in itertools.product(*sma_grid.values())]
    # Filter out invalid SMA combinations (short >= long)
    sma_values = [p for p in sma_values if p['sma_short_window'] < p['sma_long_window']]
    combinations.extend(sma_values)

    return combinations

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Quantitative Backtester - Parameter Sweep ---")
    start_time = time.time()

    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Load Data (Load once)
    print(f"\nLoading data from: {DATA_FILEPATH}")
    data = load_data(DATA_FILEPATH)

    if data is None or data.empty:
        print("\nFailed to load data. Exiting.")
        exit()

    # 2. Generate Parameter Combinations
    parameter_combinations = generate_parameter_combinations(param_grid)
    print(f"\nGenerated {len(parameter_combinations)} parameter combinations to test.")

    all_results = []
    best_sharpe = -np.inf
    best_portfolio = None
    best_params = None
    best_metrics = None

    # 3. Loop Through Combinations and Run Backtests
    for i, params in enumerate(parameter_combinations):
        print(f"\nRunning Combination {i+1}/{len(parameter_combinations)}: {params}")
        strategy = None
        signals = None
        portfolio = None
        metrics = {}

        try:
            # Initialize Strategy based on type
            if params['strategy_type'] == 'momentum':
                 strategy = MomentumStrategy(data, window=params['momentum_window'])
            elif params['strategy_type'] == 'mean_reversion':
                 strategy = MeanReversionStrategy(data, window=params['mean_reversion_window'],
                                                 entry_z=params['mean_reversion_entry_z'],
                                                 exit_z=params['mean_reversion_exit_z'])
            elif params['strategy_type'] == 'sma_crossover':
                 strategy = SMACrossoverStrategy(data, short_window=params['sma_short_window'],
                                                 long_window=params['sma_long_window'])

            # Generate Signals
            if strategy:
                signals = strategy.generate_signals()

            # Run Backtest
            if signals is not None and not signals.empty:
                 portfolio = run_backtest(data, signals,
                                          initial_capital=INITIAL_CAPITAL,
                                          allow_shorting=params['allow_shorting'])

            # Calculate Metrics
            if portfolio is not None and not portfolio.empty:
                metrics = calculate_performance_metrics(portfolio, risk_free_rate=RISK_FREE_RATE)
                print(f"  -> Result: Sharpe={metrics.get('Annualized Sharpe Ratio', np.nan):.2f}, CAGR={metrics.get('CAGR', np.nan):.2%}, MaxDD={metrics.get('Max Drawdown', np.nan):.2%}")

                # Track best result (e.g., based on Sharpe Ratio)
                current_sharpe = metrics.get('Annualized Sharpe Ratio', -np.inf)
                if pd.notna(current_sharpe) and current_sharpe > best_sharpe:
                    best_sharpe = current_sharpe
                    best_portfolio = portfolio.copy() # Store copy of best portfolio
                    best_params = params.copy()
                    best_metrics = metrics.copy()

            else:
                print("  -> Result: Backtest failed or produced empty portfolio.")
                # Ensure metrics dict has NaN values if backtest failed
                if not metrics:
                    keys = ['CAGR', 'Annualized Sharpe Ratio', 'Annualized Sortino Ratio', 'Max Drawdown', 'Calmar Ratio', 'Cumulative Return', 'Annualized Volatility', 'Total Trades']
                    for k in keys: metrics[k] = np.nan


        except ValueError as e:
            print(f"  -> Error during initialization/backtest: {e}")
            # Ensure metrics dict has NaN values if error occurred
            if not metrics:
                keys = ['CAGR', 'Annualized Sharpe Ratio', 'Annualized Sortino Ratio', 'Max Drawdown', 'Calmar Ratio', 'Cumulative Return', 'Annualized Volatility', 'Total Trades']
                for k in keys: metrics[k] = np.nan
        except Exception as e:
            print(f"  -> An unexpected error occurred: {e}")
            # Ensure metrics dict has NaN values
            if not metrics:
                keys = ['CAGR', 'Annualized Sharpe Ratio', 'Annualized Sortino Ratio', 'Max Drawdown', 'Calmar Ratio', 'Cumulative Return', 'Annualized Volatility', 'Total Trades']
                for k in keys: metrics[k] = np.nan


        # Store result (parameters + metrics)
        run_result = params.copy()
        run_result.update(metrics)
        all_results.append(run_result)

    # 4. Process and Display Results
    print("\n--- Backtesting Finished ---")
    results_df = pd.DataFrame(all_results)

    # Basic Formatting for display
    float_cols = ['CAGR', 'Annualized Sharpe Ratio', 'Annualized Sortino Ratio',
                  'Max Drawdown', 'Calmar Ratio', 'Cumulative Return', 'Annualized Volatility']
    formatters = {}
    for col in float_cols:
        if col in results_df.columns:
             # Format percentages, keep ratios/others as floats for sorting
             if "Ratio" in col or "Return" in col or "CAGR" in col or "Volatility" in col or "Drawdown" in col:
                 formatters[col] = '{:.2%}'.format
             else:
                 formatters[col] = '{:.4f}'.format

    # Sort by Sharpe Ratio (descending), handle NaNs
    results_df.sort_values(by='Annualized Sharpe Ratio', ascending=False, inplace=True, na_position='last')

    print("\n--- Top 5 Results (Sorted by Sharpe Ratio) ---")
    print(results_df.head(5).to_string(formatters=formatters))

    # Save all results to CSV
    results_filename = os.path.join(OUTPUT_DIR, 'all_backtest_results.csv')
    try:
        results_df.to_csv(results_filename, index=False, float_format='%.4f')
        print(f"\nFull results saved to: {results_filename}")
    except Exception as e:
        print(f"Error saving results to CSV: {e}")

    # 5. Plot the Best Result
    if best_portfolio is not None and best_params is not None:
        print(f"\n--- Best Performing Combination (Sharpe = {best_sharpe:.3f}) ---")
        print(best_params)
        print("Metrics:")
        for key, value in best_metrics.items():
            if isinstance(value, float):
                 if "Ratio" in key or "CAGR" in key or "Return" in key or "Volatility" in key or "Drawdown" in key :
                     print(f"  {key}: {value:.2%}")
                 else:
                      print(f"  {key}: {value:.4f}")
            else:
                 print(f"  {key}: {value}")

        plot_title = f"Best Strategy: {best_params.get('strategy_type','N/A').replace('_',' ').title()} " \
                     f"(Sharpe: {best_sharpe:.2f})"
        plot_filename = os.path.join(OUTPUT_DIR, f"best_strategy_plot_{best_params.get('strategy_type','default')}.png")
        plot_equity_curve(best_portfolio, title=plot_title, filename=plot_filename)
    else:
        print("\nNo successful backtest runs found to determine the best performance.")

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")
    print("--- Run Complete ---")