import numpy as np
import pandas as pd

# ... (keep calculate_cagr, calculate_sharpe, calculate_sortino, calculate_max_drawdown, calculate_calmar as before) ...
def calculate_cagr(portfolio_value):
    """Calculates Compound Annual Growth Rate (CAGR)."""
    if portfolio_value is None or portfolio_value.empty or len(portfolio_value) < 2: return np.nan
    start_value = portfolio_value.iloc[0]
    end_value = portfolio_value.iloc[-1]
    # Ensure start_value is not zero or negative before proceeding
    if start_value <= 0: return np.nan

    start_date = portfolio_value.index[0]
    end_date = portfolio_value.index[-1]
    num_years = (end_date - start_date).days / 365.25

    if num_years <= 0: return np.nan # Avoid issues with very short periods

    # Use np.sign to handle potential negative end_value gracefully in calculation if needed, though unlikely with equity curves
    cagr = (np.sign(end_value) * np.abs(end_value / start_value)) ** (1 / num_years) - 1
    # Handle potential complex numbers if end_value was negative and num_years fractional in a weird way
    if isinstance(cagr, complex):
        return np.nan # Or handle appropriately
    return cagr

def calculate_sharpe(returns, risk_free_rate=0.0):
    """Calculates annualized Sharpe Ratio."""
    if returns is None or len(returns) < 2: return np.nan
    # Ensure returns is numeric and handle potential NaNs before std calculation
    returns = pd.to_numeric(returns, errors='coerce').dropna()
    if len(returns) < 2: return np.nan

    excess_returns = returns - risk_free_rate / 252 # Daily risk-free rate
    mean_excess_return = excess_returns.mean()
    std_dev = excess_returns.std()

    if std_dev is None or std_dev == 0 or pd.isna(std_dev):
        return np.nan # Avoid division by zero or NaN std dev

    sharpe_ratio = mean_excess_return / std_dev
    annualized_sharpe = sharpe_ratio * np.sqrt(252) # Assuming daily returns
    return annualized_sharpe

def calculate_sortino(returns, risk_free_rate=0.0):
    """Calculates annualized Sortino Ratio."""
    if returns is None or len(returns) < 2: return np.nan
    # Ensure returns is numeric and handle potential NaNs
    returns = pd.to_numeric(returns, errors='coerce').dropna()
    if len(returns) < 2: return np.nan

    excess_returns = returns - risk_free_rate / 252

    # Calculate downside deviation (std dev of negative excess returns)
    negative_excess_returns = excess_returns[excess_returns < 0]

    if negative_excess_returns.empty:
        # If no downside returns, Sortino is arguably infinite (or very high)
        # Check if mean excess return is positive, if so, return large number, else NaN
        if excess_returns.mean() > 0:
            return np.inf
        else:
            return np.nan

    downside_deviation = negative_excess_returns.std()

    if downside_deviation is None or downside_deviation == 0 or pd.isna(downside_deviation):
        # If downside deviation is zero (and mean return > 0), ratio is infinite
        if excess_returns.mean() > 0:
            return np.inf
        else:
             return np.nan # Avoid division by zero if mean is also zero/negative

    sortino_ratio = excess_returns.mean() / downside_deviation
    annualized_sortino = sortino_ratio * np.sqrt(252) # Assuming daily returns
    return annualized_sortino


def calculate_max_drawdown(portfolio_value):
    """Calculates Maximum Drawdown."""
    if portfolio_value is None or portfolio_value.empty or len(portfolio_value) < 2: return np.nan
    # Ensure values are numeric
    portfolio_value = pd.to_numeric(portfolio_value, errors='coerce').dropna()
    if len(portfolio_value) < 2: return np.nan
    if (portfolio_value <= 0).any():
        print("Warning: Non-positive portfolio values found. Max Drawdown calculation might be unreliable.")
        # Decide handling: return NaN, or try to proceed? Let's return NaN for safety.
        return np.nan

    cumulative_returns = portfolio_value / portfolio_value.iloc[0] # Normalize to 1
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min() # Min value represents the largest percentage drop

    return max_drawdown


def calculate_calmar(cagr, max_drawdown):
    """Calculates Calmar Ratio."""
    if max_drawdown is None or max_drawdown == 0 or pd.isna(cagr) or pd.isna(max_drawdown):
        return np.nan # Avoid division by zero or NaN input
    # Ensure max_drawdown is negative (conventionally) before taking absolute value
    if max_drawdown > 0: max_drawdown = -max_drawdown

    calmar = cagr / abs(max_drawdown)
    return calmar


def calculate_performance_metrics(portfolio, risk_free_rate=0.0):
    """Calculates and returns a dictionary of key performance metrics."""
    metrics = {} # Initialize empty dict

    if portfolio is None or portfolio.empty or 'equity_curve' not in portfolio or 'strategy_return' not in portfolio:
        print("Warning: Cannot calculate metrics on invalid or empty portfolio DataFrame.")
        # Return dict with NaNs
        keys = ['CAGR', 'Annualized Sharpe Ratio', 'Annualized Sortino Ratio', 'Max Drawdown', 'Calmar Ratio', 'Cumulative Return', 'Annualized Volatility']
        for k in keys: metrics[k] = np.nan
        return metrics

    equity_curve = portfolio['equity_curve']
    strategy_returns = portfolio['strategy_return']

    if equity_curve.empty or strategy_returns.empty:
         print("Warning: Equity curve or strategy returns are empty.")
         keys = ['CAGR', 'Annualized Sharpe Ratio', 'Annualized Sortino Ratio', 'Max Drawdown', 'Calmar Ratio', 'Cumulative Return', 'Annualized Volatility']
         for k in keys: metrics[k] = np.nan
         return metrics


    # print("\nCalculating performance metrics...") # Reduced verbosity

    metrics['CAGR'] = calculate_cagr(equity_curve)
    metrics['Annualized Sharpe Ratio'] = calculate_sharpe(strategy_returns, risk_free_rate)
    metrics['Annualized Sortino Ratio'] = calculate_sortino(strategy_returns, risk_free_rate)
    metrics['Max Drawdown'] = calculate_max_drawdown(equity_curve)
    metrics['Calmar Ratio'] = calculate_calmar(metrics['CAGR'], metrics['Max Drawdown'])

    # Add some other basic stats
    metrics['Cumulative Return'] = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1 if not equity_curve.empty and equity_curve.iloc[0] != 0 else np.nan
    metrics['Annualized Volatility'] = strategy_returns.std() * np.sqrt(252) if not strategy_returns.empty else np.nan
    metrics['Total Trades'] = portfolio['position'].diff().fillna(0).abs().sum() / 2 # Estimate trades

    # print("Performance metrics calculated.") # Reduced verbosity
    return metrics