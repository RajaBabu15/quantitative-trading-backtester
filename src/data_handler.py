import pandas as pd
import os

def load_data(filepath):
    """
    Loads historical stock data from a CSV file.

    Args:
        filepath (str): The path to the CSV file.
                        Expected columns: 'Date', 'Adj Close'.
                        'Date' should be the index or the first column.

    Returns:
        pandas.DataFrame: DataFrame with 'Date' as index and 'Adj Close'.
                          Returns None if file not found or error occurs.
    """
    if not os.path.exists(filepath):
        print(f"Error: Data file not found at {filepath}")
        return None

    try:
        # Try reading with 'Date' as the first column to be parsed as index
        df = pd.read_csv(filepath, index_col='Date', parse_dates=True)

        if 'Adj Close' not in df.columns:
            print("Error: 'Adj Close' column not found in the data.")
            return None

        # Keep only the 'Adj Close' column, rename for consistency if needed
        df = df[['Adj Close']].copy()
        df.sort_index(inplace=True) # Ensure data is chronologically sorted
        print(f"Data loaded successfully: {len(df)} rows from {df.index.min()} to {df.index.max()}")
        return df

    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return None