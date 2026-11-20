"""
Update Indian stock data from Yahoo Finance (2022-01-01 to present)
Run this script to fetch latest data and update indian_stocks.csv
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Indian stock tickers (NSE)
TICKERS = [
    "TCS.NS",          # Tata Consultancy Services
    "INFY.NS",         # Infosys
    "WIPRO.NS",        # Wipro
    "HCLTECH.NS",      # HCL Technologies
    "RELIANCE.NS",     # Reliance Industries
    "HDFCBANK.NS",     # HDFC Bank
    "ICICIBANK.NS",    # ICICI Bank
    "ITC.NS",          # ITC Limited
    "SBIN.NS",         # State Bank of India
    "ASIANPAINT.NS",   # Asian Paints
    "BHARTIARTL.NS",   # Bharti Airtel
    "TATAMOTORS.NS",   # Tata Motors
    "ADANIENT.NS",     # Adani Enterprises
    "BAJFINANCE.NS",   # Bajaj Finance
    "LT.NS",           # Larsen & Toubro
    "AXISBANK.NS",     # Axis Bank
    "MARUTI.NS",       # Maruti Suzuki
    "SUNPHARMA.NS",    # Sun Pharma
    "TITAN.NS",        # Titan Company
    "HINDUNILVR.NS",   # Hindustan Unilever
]

START_DATE = "2022-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

DATA_DIR = Path(__file__).parent / "data"
CSV_FILE = DATA_DIR / "indian_stocks.csv"


def fetch_stock_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch stock data from Yahoo Finance for a single ticker."""
    try:
        logger.info(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, end=end, auto_adjust=False)
        
        if df.empty:
            logger.warning(f"No data found for {ticker}")
            return pd.DataFrame()
        
        # Reset index to get Date as a column
        df = df.reset_index()
        
        # Add ticker column
        df['Ticker'] = ticker
        
        # Select and rename columns to match existing format
        df = df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Convert Date to string format (YYYY-MM-DD)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        logger.info(f"✓ Fetched {len(df)} rows for {ticker}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()


def update_stock_data():
    """Fetch and update stock data for all tickers."""
    logger.info(f"Starting data update from {START_DATE} to {END_DATE}")
    logger.info(f"Total tickers: {len(TICKERS)}")
    
    all_data = []
    
    for ticker in TICKERS:
        df = fetch_stock_data(ticker, START_DATE, END_DATE)
        if not df.empty:
            all_data.append(df)
    
    if not all_data:
        logger.error("No data fetched! Check your internet connection.")
        return
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Sort by Date and Ticker
    combined_df = combined_df.sort_values(['Date', 'Ticker']).reset_index(drop=True)
    
    # Save to CSV
    DATA_DIR.mkdir(exist_ok=True)
    combined_df.to_csv(CSV_FILE, index=False)
    
    logger.info("=" * 70)
    logger.info("✅ DATA UPDATE COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"Total rows: {len(combined_df):,}")
    logger.info(f"Date range: {combined_df['Date'].min()} to {combined_df['Date'].max()}")
    logger.info(f"Tickers: {combined_df['Ticker'].nunique()}")
    logger.info(f"File saved: {CSV_FILE}")
    logger.info("=" * 70)
    
    # Show sample data
    print("\nSample data (latest 5 rows per ticker):")
    for ticker in TICKERS[:3]:  # Show first 3 tickers as sample
        ticker_data = combined_df[combined_df['Ticker'] == ticker].tail(5)
        if not ticker_data.empty:
            print(f"\n{ticker}:")
            print(ticker_data[['Date', 'Close', 'Volume']].to_string(index=False))


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     Indian Stock Data Updater (Yahoo Finance)            ║
    ║     Fetching data from 2022-01-01 to present           ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    update_stock_data()
