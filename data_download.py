import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def download_spy_data():
    # Calculate date range (5 years from today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    # Download SPY data
    spy = yf.Ticker("SPY")
    df = spy.history(start=start_date, end=end_date)
    
    # Reset index to make Date a column and drop unwanted columns
    df = df.reset_index()
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    
    # Add Adj Close column (same as Close for now, as it's already adjusted)
    df['Adj Close'] = df['Close']
    
    # Reorder columns to match required format
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    
    # Ensure Date is in YYYY-MM-DD format
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    # Round numeric columns to 6 decimal places for cleaner output
    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close']
    df[numeric_columns] = df[numeric_columns].round(6)
    
    # Save to CSV
    df.to_csv('data/sample_data.csv', index=False)
    print(f"Successfully downloaded {len(df)} days of SPY data to data/sample_data.csv")
    print("\nFirst few rows of the data:")
    print(df.head().to_string())

if __name__ == "__main__":
    download_spy_data()
