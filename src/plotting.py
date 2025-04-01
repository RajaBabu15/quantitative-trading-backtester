import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

def plot_equity_curve(portfolio, title='Strategy Performance', filename=None):
    """
    Plots the equity curve against the benchmark (market).
    Optionally saves the plot to a file.
    """
    if portfolio is None or portfolio.empty:
        print("Warning: Cannot plot empty portfolio.")
        return

    fig, ax = plt.subplots(figsize=(14, 8)) # Slightly larger plot

    # Plot Equity Curve
    ax.plot(portfolio.index, portfolio['equity_curve'], label='Strategy Equity', color='blue', linewidth=1.5)

    # Plot Benchmark (Market Cumulative Return scaled by initial capital)
    initial_capital = portfolio['equity_curve'].iloc[0] / portfolio['cumulative_strategy'].iloc[0] if portfolio['cumulative_strategy'].iloc[0] != 0 else portfolio['equity_curve'].iloc[0]
    benchmark_equity = initial_capital * portfolio['cumulative_market']
    ax.plot(portfolio.index, benchmark_equity, label=f'Market (Buy & Hold - Start: ${initial_capital:,.0f})', color='grey', linestyle='--', linewidth=1.0)

    # Formatting
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, linestyle=':', alpha=0.6)

    # Improve Date Formatting
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(years_fmt)
    ax.xaxis.set_minor_locator(months)
    fig.autofmt_xdate() # Auto format date labels for readability

    # Add Final Value Annotations
    final_strat_val = portfolio['equity_curve'].iloc[-1]
    final_bench_val = benchmark_equity.iloc[-1]
    ax.annotate(f'Strategy Final: ${final_strat_val:,.0f}',
                xy=(portfolio.index[-1], final_strat_val),
                xytext=(10, -10), textcoords='offset points', ha='left', va='top',
                bbox=dict(boxstyle='round,pad=0.3', fc='lightblue', alpha=0.5))
    ax.annotate(f'Benchmark Final: ${final_bench_val:,.0f}',
                xy=(portfolio.index[-1], final_bench_val),
                xytext=(10, 10), textcoords='offset points', ha='left', va='bottom',
                bbox=dict(boxstyle='round,pad=0.3', fc='lightgrey', alpha=0.5))


    plt.tight_layout() # Adjust layout to prevent labels overlapping

    # Save the plot if filename is provided
    if filename:
        try:
            # Ensure the directory exists if specified in the filename
            plot_dir = os.path.dirname(filename)
            if plot_dir and not os.path.exists(plot_dir):
                os.makedirs(plot_dir)
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {filename}")
            plt.close(fig) # Close the plot window after saving
        except Exception as e:
            print(f"Error saving plot to {filename}: {e}")
            plt.show() # Show plot if saving failed
    else:
        print("Displaying plot...")
        plt.show()