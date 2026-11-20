"""Seed the interface library with pre-built common stock analysis functions.

This pre-generates interfaces for common queries to avoid cold-start latency.
"""

from model.tools import interface_library
from model.retriever import ToolRetriever
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pre-built interfaces for common stock queries - 50 interfaces covering diverse use cases
SEED_INTERFACES = [
    {
        "name": "get_current_price",
        "description": "Get the most recent closing price, current price, latest price, stock price today, present price, today's price for a stock ticker. Use for queries like: current price, latest price, stock price today, what is the price, how much is trading at, present price, today's price, what is trading at, stock value, price now",
        "code": """def get_current_price(ticker: str) -> dict:
    \"\"\"Get the most recent closing price for a ticker.\"\"\"
    df = _load_data()
    stock_data = df[df["Ticker"] == ticker]
    if stock_data.empty:
        return {"error": f"No data found for {ticker}"}
    latest = stock_data.sort_values("Date", ascending=False).iloc[0]
    return {
        "ticker": ticker,
        "date": str(latest["Date"]),
        "price": float(latest["Close"]),
        "open": float(latest["Open"]),
        "high": float(latest["High"]),
        "low": float(latest["Low"]),
        "volume": int(latest["Volume"])
    }""",
        "test_query": "What is the current price of TCS?",
    },
    {
        "name": "compare_two_stocks",
        "description": "Compare price trends of two stocks over a time period with a chart",
        "code": """def compare_two_stocks(ticker1: str, ticker2: str, start_date: str, end_date: str) -> dict:
    \"\"\"Compare two stocks' closing prices over time.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    df1 = df[(df["Ticker"] == ticker1) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]
    df2 = df[(df["Ticker"] == ticker2) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]
    
    if df1.empty or df2.empty:
        return {"error": "Insufficient data for comparison"}
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df1["Date"], df1["Close"], label=ticker1, linewidth=2)
    ax.plot(df2["Date"], df2["Close"], label=ticker2, linewidth=2)
    ax.set_xlabel("Date")
    ax.set_ylabel("Close Price (₹)")
    ax.set_title(f"{ticker1} vs {ticker2} Comparison")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{ticker1.replace('.', '_')}_vs_{ticker2.replace('.', '_')}_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return {
        "ticker1": ticker1,
        "ticker2": ticker2,
        "ticker1_final_price": float(df1.iloc[-1]["Close"]),
        "ticker2_final_price": float(df2.iloc[-1]["Close"]),
        "ticker1_return_pct": float((df1.iloc[-1]["Close"] - df1.iloc[0]["Close"]) / df1.iloc[0]["Close"] * 100),
        "ticker2_return_pct": float((df2.iloc[-1]["Close"] - df2.iloc[0]["Close"]) / df2.iloc[0]["Close"] * 100),
        "chart_path": str(chart_path)
    }""",
        "test_query": "Compare TCS and Infosys performance in 2024",
    },
    {
        "name": "plot_stock_trend",
        "description": "Plot price trend, line chart, stock chart, show stock data, visualize stock price, stock performance chart for a single stock over any date range or year. Use for queries like: show chart, plot trend, line chart, stock data visualization, price movement, historical data chart",
        "code": """def plot_stock_trend(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Plot stock price trend over time.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]
    
    if stock_data.empty:
        return {"error": f"No data for {ticker} in the given date range"}
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(stock_data["Date"], stock_data["Close"], linewidth=2, color='#2E86AB')
    ax.fill_between(stock_data["Date"], stock_data["Close"], alpha=0.3, color='#2E86AB')
    ax.set_xlabel("Date")
    ax.set_ylabel("Close Price (₹)")
    ax.set_title(f"{ticker} Price Trend ({start_date} to {end_date})")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{ticker.replace('.', '_')}_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    start_price = float(stock_data.iloc[0]["Close"])
    end_price = float(stock_data.iloc[-1]["Close"])
    return_pct = (end_price - start_price) / start_price * 100
    
    return {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "start_price": start_price,
        "end_price": end_price,
        "return_pct": return_pct,
        "min_price": float(stock_data["Close"].min()),
        "max_price": float(stock_data["Close"].max()),
        "chart_path": str(chart_path)
    }""",
        "test_query": "Show me TCS stock trend in 2024",
    },
    {
        "name": "get_stock_statistics",
        "description": "Calculate statistical summary (mean, std, min, max) for a stock",
        "code": """def get_stock_statistics(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Get statistical summary for a stock in a date range.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]
    
    if stock_data.empty:
        return {"error": f"No data for {ticker}"}
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "mean_close": float(stock_data["Close"].mean()),
        "std_close": float(stock_data["Close"].std()),
        "min_close": float(stock_data["Close"].min()),
        "max_close": float(stock_data["Close"].max()),
        "mean_volume": int(stock_data["Volume"].mean()),
        "total_trading_days": len(stock_data)
    }""",
        "test_query": "What are the statistics for Reliance stock in 2023?",
    },
    {
        "name": "calculate_moving_average",
        "description": "Calculate and plot moving average for a stock",
        "code": """def calculate_moving_average(ticker: str, window: int, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate moving average and plot it with price.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < window:
        return {"error": f"Insufficient data for {window}-day MA"}
    
    stock_data["MA"] = stock_data["Close"].rolling(window=window).mean()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(stock_data["Date"], stock_data["Close"], label="Close Price", linewidth=2)
    ax.plot(stock_data["Date"], stock_data["MA"], label=f"{window}-day MA", linewidth=2, linestyle='--')
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (₹)")
    ax.set_title(f"{ticker} with {window}-day Moving Average")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{ticker.replace('.', '_')}_ma_{window}_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return {
        "ticker": ticker,
        "window": window,
        "latest_price": float(stock_data.iloc[-1]["Close"]),
        "latest_ma": float(stock_data.iloc[-1]["MA"]),
        "chart_path": str(chart_path)
    }""",
        "test_query": "Show 50-day moving average for TCS in 2024",
    },
    {
        "name": "compare_multiple_stocks",
        "description": "Compare 3 or more stocks on the same chart",
        "code": """def compare_multiple_stocks(tickers: list, start_date: str, end_date: str) -> dict:
    \"\"\"Compare multiple stocks' normalized returns.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    results = {}
    
    for ticker in tickers:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
        if not stock_data.empty:
            # Normalize to 100 at start
            normalized = (stock_data["Close"] / stock_data["Close"].iloc[0]) * 100
            ax.plot(stock_data["Date"], normalized, label=ticker, linewidth=2)
            results[ticker] = {
                "final_value": float(normalized.iloc[-1]),
                "return_pct": float(normalized.iloc[-1] - 100)
            }
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Value (Base 100)")
    ax.set_title(f"Multi-Stock Comparison ({start_date} to {end_date})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    tickers_str = "_vs_".join([t.replace(".", "_") for t in tickers])
    chart_path = settings.charts_dir / f"multi_{tickers_str}_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return {
        "tickers": tickers,
        "period": f"{start_date} to {end_date}",
        "results": results,
        "chart_path": str(chart_path)
    }""",
        "test_query": "Compare TCS, Infosys, Wipro, and HCL Tech in 2023",
    },
    {
        "name": "get_yearly_high_low",
        "description": "Get the highest and lowest prices for a stock in a given year",
        "code": """def get_yearly_high_low(ticker: str, year: int) -> dict:
    \"\"\"Get yearly high and low prices for a stock.\"\"\"
    import pandas as pd
    
    df = _load_data()
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])
    
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"].dt.year == year)]
    
    if stock_data.empty:
        return {"error": f"No data for {ticker} in {year}"}
    
    high_row = stock_data.loc[stock_data["High"].idxmax()]
    low_row = stock_data.loc[stock_data["Low"].idxmin()]
    
    return {
        "ticker": ticker,
        "year": year,
        "yearly_high": float(high_row["High"]),
        "high_date": str(high_row["Date"].date()) if hasattr(high_row["Date"], 'date') else str(high_row["Date"]),
        "yearly_low": float(low_row["Low"]),
        "low_date": str(low_row["Date"].date()) if hasattr(low_row["Date"], 'date') else str(low_row["Date"]),
        "range": float(high_row["High"] - low_row["Low"])
    }""",
        "test_query": "What was the highest and lowest price of Reliance in 2024?",
    },
    {
        "name": "calculate_stock_volatility",
        "description": "Calculate volatility (standard deviation of returns) for a stock",
        "code": """def calculate_stock_volatility(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate stock volatility based on daily returns.\"\"\"
    import numpy as np
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 2:
        return {"error": "Insufficient data"}
    
    # Calculate daily returns
    stock_data["returns"] = stock_data["Close"].pct_change()
    
    volatility = float(stock_data["returns"].std())
    mean_return = float(stock_data["returns"].mean())
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "volatility": volatility,
        "annualized_volatility": volatility * np.sqrt(252),  # 252 trading days
        "mean_daily_return": mean_return,
        "max_daily_gain": float(stock_data["returns"].max()),
        "max_daily_loss": float(stock_data["returns"].min())
    }""",
        "test_query": "What is the volatility of HDFC Bank in 2024?",
    },
    {
        "name": "get_average_volume",
        "description": "Calculate average trading volume for a stock",
        "code": """def get_average_volume(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Get average trading volume for a stock.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]
    
    if stock_data.empty:
        return {"error": f"No data for {ticker}"}
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "average_volume": int(stock_data["Volume"].mean()),
        "max_volume": int(stock_data["Volume"].max()),
        "max_volume_date": str(stock_data.loc[stock_data["Volume"].idxmax(), "Date"]),
        "min_volume": int(stock_data["Volume"].min()),
        "total_volume": int(stock_data["Volume"].sum())
    }""",
        "test_query": "What is the average trading volume for ITC in 2023?",
    },
    {
        "name": "find_best_performing_stock",
        "description": "Find the best performing stock from a list in a time period",
        "code": """def find_best_performing_stock(tickers: list, start_date: str, end_date: str) -> dict:
    \"\"\"Find which stock had the highest return in the period.\"\"\"
    df = _load_data()
    
    performances = {}
    for ticker in tickers:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
        if not stock_data.empty and len(stock_data) >= 2:
            start_price = float(stock_data.iloc[0]["Close"])
            end_price = float(stock_data.iloc[-1]["Close"])
            return_pct = (end_price - start_price) / start_price * 100
            performances[ticker] = {
                "return_pct": return_pct,
                "start_price": start_price,
                "end_price": end_price
            }
    
    if not performances:
        return {"error": "No data available"}
    
    best_ticker = max(performances.keys(), key=lambda x: performances[x]["return_pct"])
    worst_ticker = min(performances.keys(), key=lambda x: performances[x]["return_pct"])
    
    return {
        "period": f"{start_date} to {end_date}",
        "best_performer": best_ticker,
        "best_return": performances[best_ticker]["return_pct"],
        "worst_performer": worst_ticker,
        "worst_return": performances[worst_ticker]["return_pct"],
        "all_performances": performances
    }""",
        "test_query": "Which IT stock performed best in 2024?",
    },
    # ══════════════════════════════════════════════════════════
    # ADDITIONAL 40 INTERFACES FOR COMPREHENSIVE COVERAGE
    # ══════════════════════════════════════════════════════════
    {
        "name": "get_stock_price_on_date",
        "description": "Get stock price on a specific date",
        "code": """def get_stock_price_on_date(ticker: str, date: str) -> dict:
    \"\"\"Get stock price on a specific date.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] == date)]
    
    if stock_data.empty:
        return {"error": f"No data for {ticker} on {date}"}
    
    row = stock_data.iloc[0]
    return {
        "ticker": ticker,
        "date": date,
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
        "volume": int(row["Volume"])
    }""",
        "test_query": "What was TCS price on 2024-01-15?",
    },
    {
        "name": "calculate_stock_return",
        "description": "Calculate percentage return between two dates",
        "code": """def calculate_stock_return(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate return percentage between two dates.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 2:
        return {"error": "Insufficient data"}
    
    start_price = float(stock_data.iloc[0]["Close"])
    end_price = float(stock_data.iloc[-1]["Close"])
    return_pct = ((end_price - start_price) / start_price) * 100
    
    return {
        "ticker": ticker,
        "start_date": str(stock_data.iloc[0]["Date"]),
        "end_date": str(stock_data.iloc[-1]["Date"]),
        "start_price": start_price,
        "end_price": end_price,
        "absolute_return": end_price - start_price,
        "return_percentage": return_pct
    }""",
        "test_query": "What was the return on Infosys from Jan 2024 to Dec 2024?",
    },
    {
        "name": "plot_candlestick_chart",
        "description": "Create a candlestick chart for stock OHLC data",
        "code": """def plot_candlestick_chart(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Plot candlestick chart showing OHLC data.\"\"\"
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from pathlib import Path
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for idx, row in stock_data.iterrows():
        color = 'green' if row['Close'] >= row['Open'] else 'red'
        # Draw high-low line
        ax.plot([idx, idx], [row['Low'], row['High']], color=color, linewidth=1)
        # Draw open-close box
        height = abs(row['Close'] - row['Open'])
        bottom = min(row['Open'], row['Close'])
        ax.add_patch(mpatches.Rectangle((idx-0.3, bottom), 0.6, height, 
                                         facecolor=color, edgecolor=color, alpha=0.8))
    
    ax.set_title(f"{ticker} Candlestick Chart ({start_date} to {end_date})")
    ax.set_ylabel("Price (₹)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{ticker.replace('.', '_')}_candlestick_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return {
        "ticker": ticker,
        "data_points": len(stock_data),
        "chart_path": str(chart_path)
    }""",
        "test_query": "Show me a candlestick chart for Reliance in October 2024",
    },
    {
        "name": "compare_sector_performance",
        "description": "Compare performance of stocks from the same sector",
        "code": """def compare_sector_performance(sector: str, tickers: list, start_date: str, end_date: str) -> dict:
    \"\"\"Compare performance of stocks in a sector.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    results = {}
    
    for ticker in tickers:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
        if not stock_data.empty and len(stock_data) >= 2:
            start_price = float(stock_data.iloc[0]["Close"])
            end_price = float(stock_data.iloc[-1]["Close"])
            return_pct = ((end_price - start_price) / start_price) * 100
            
            # Plot normalized
            normalized = (stock_data["Close"] / start_price) * 100
            ax.plot(stock_data["Date"], normalized, label=ticker, linewidth=2)
            
            results[ticker] = {
                "return_pct": return_pct,
                "start_price": start_price,
                "end_price": end_price
            }
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Value (Base 100)")
    ax.set_title(f"{sector} Sector Performance Comparison")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{sector.lower().replace(' ', '_')}_comparison_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return {
        "sector": sector,
        "period": f"{start_date} to {end_date}",
        "results": results,
        "chart_path": str(chart_path)
    }""",
        "test_query": "Compare IT sector stocks in 2024",
    },
    {
        "name": "get_monthly_returns",
        "description": "Calculate monthly returns for a stock",
        "code": """def get_monthly_returns(ticker: str, year: int) -> dict:
    \"\"\"Get monthly returns for a stock in a given year.\"\"\"
    import pandas as pd
    
    df = _load_data()
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])
        
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"].dt.year == year)].copy()
    
    if stock_data.empty:
        return {"error": f"No data for {ticker} in {year}"}
    
    stock_data["Month"] = stock_data["Date"].dt.to_period('M')
    
    monthly_data = stock_data.groupby("Month").agg({
        "Close": ["first", "last"]
    }).reset_index()
    
    monthly_data.columns = ["Month", "First", "Last"]
    monthly_data["Return_Pct"] = ((monthly_data["Last"] - monthly_data["First"]) / monthly_data["First"]) * 100
    
    monthly_returns = {str(row["Month"]): float(row["Return_Pct"]) for _, row in monthly_data.iterrows()}
    
    return {
        "ticker": ticker,
        "year": year,
        "monthly_returns": monthly_returns,
        "average_monthly_return": float(monthly_data["Return_Pct"].mean()),
        "best_month": str(monthly_data.loc[monthly_data["Return_Pct"].idxmax(), "Month"]),
        "worst_month": str(monthly_data.loc[monthly_data["Return_Pct"].idxmin(), "Month"])
    }""",
        "test_query": "What were the monthly returns for HDFC Bank in 2024?",
    },
    {
        "name": "calculate_correlation",
        "description": "Calculate price correlation between two stocks",
        "code": """def calculate_correlation(ticker1: str, ticker2: str, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate correlation coefficient between two stocks.\"\"\"
    df = _load_data()
    
    df1 = df[(df["Ticker"] == ticker1) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    df2 = df[(df["Ticker"] == ticker2) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    # Merge on date
    merged = df1[["Date", "Close"]].merge(df2[["Date", "Close"]], on="Date", suffixes=("_1", "_2"))
    
    if len(merged) < 2:
        return {"error": "Insufficient overlapping data"}
    
    correlation = float(merged["Close_1"].corr(merged["Close_2"]))
    
    return {
        "ticker1": ticker1,
        "ticker2": ticker2,
        "period": f"{start_date} to {end_date}",
        "correlation": correlation,
        "data_points": len(merged),
        "interpretation": "Strong positive" if correlation > 0.7 else "Moderate positive" if correlation > 0.3 else "Weak/Negative"
    }""",
        "test_query": "What is the correlation between TCS and Infosys in 2024?",
    },
    {
        "name": "find_biggest_gainers",
        "description": "Find stocks with highest single-day gains",
        "code": """def find_biggest_gainers(tickers: list, start_date: str, end_date: str, top_n: int = 5) -> dict:
    \"\"\"Find biggest single-day percentage gainers.\"\"\"
    df = _load_data()
    
    all_gains = []
    for ticker in tickers:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
        if not stock_data.empty:
            stock_data["Daily_Return"] = stock_data["Close"].pct_change() * 100
            for _, row in stock_data.iterrows():
                if pd.notna(row["Daily_Return"]):
                    all_gains.append({
                        "ticker": ticker,
                        "date": str(row["Date"]),
                        "gain_pct": float(row["Daily_Return"]),
                        "close": float(row["Close"])
                    })
    
    all_gains.sort(key=lambda x: x["gain_pct"], reverse=True)
    
    return {
        "period": f"{start_date} to {end_date}",
        "top_gainers": all_gains[:top_n]
    }""",
        "test_query": "What were the biggest single-day gains in IT stocks in 2024?",
    },
    {
        "name": "find_biggest_losers",
        "description": "Find stocks with highest single-day losses",
        "code": """def find_biggest_losers(tickers: list, start_date: str, end_date: str, top_n: int = 5) -> dict:
    \"\"\"Find biggest single-day percentage losers.\"\"\"
    df = _load_data()
    
    all_losses = []
    for ticker in tickers:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
        if not stock_data.empty:
            stock_data["Daily_Return"] = stock_data["Close"].pct_change() * 100
            for _, row in stock_data.iterrows():
                if pd.notna(row["Daily_Return"]):
                    all_losses.append({
                        "ticker": ticker,
                        "date": str(row["Date"]),
                        "loss_pct": float(row["Daily_Return"]),
                        "close": float(row["Close"])
                    })
    
    all_losses.sort(key=lambda x: x["loss_pct"])
    
    return {
        "period": f"{start_date} to {end_date}",
        "top_losers": all_losses[:top_n]
    }""",
        "test_query": "What were the biggest single-day losses in 2024?",
    },
    {
        "name": "plot_volume_analysis",
        "description": "Plot volume alongside price to identify volume spikes",
        "code": """def plot_volume_analysis(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Plot price with volume bars to analyze volume patterns.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Price plot
    ax1.plot(stock_data["Date"], stock_data["Close"], linewidth=2, color='#2E86AB')
    ax1.set_ylabel("Close Price (₹)")
    ax1.set_title(f"{ticker} Price and Volume Analysis")
    ax1.grid(True, alpha=0.3)
    
    # Volume bars
    colors = ['green' if stock_data.iloc[i]["Close"] >= stock_data.iloc[i]["Open"] else 'red' 
              for i in range(len(stock_data))]
    ax2.bar(stock_data["Date"], stock_data["Volume"], color=colors, alpha=0.7)
    ax2.set_ylabel("Volume")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{ticker.replace('.', '_')}_volume_analysis_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    avg_volume = int(stock_data["Volume"].mean())
    max_volume_row = stock_data.loc[stock_data["Volume"].idxmax()]
    
    return {
        "ticker": ticker,
        "average_volume": avg_volume,
        "max_volume": int(max_volume_row["Volume"]),
        "max_volume_date": str(max_volume_row["Date"]),
        "chart_path": str(chart_path)
    }""",
        "test_query": "Show volume analysis for Wipro in 2024",
    },
    {
        "name": "calculate_drawdown",
        "description": "Calculate maximum drawdown (peak to trough decline)",
        "code": """def calculate_drawdown(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate maximum drawdown for a stock.\"\"\"
    import numpy as np
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    prices = stock_data["Close"].values
    cummax = np.maximum.accumulate(prices)
    drawdown = (prices - cummax) / cummax * 100
    
    max_dd_idx = np.argmin(drawdown)
    max_dd = float(drawdown[max_dd_idx])
    
    # Find peak before max drawdown
    peak_idx = np.argmax(prices[:max_dd_idx+1])
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "max_drawdown_pct": max_dd,
        "peak_price": float(prices[peak_idx]),
        "peak_date": str(stock_data.iloc[peak_idx]["Date"]),
        "trough_price": float(prices[max_dd_idx]),
        "trough_date": str(stock_data.iloc[max_dd_idx]["Date"])
    }""",
        "test_query": "What was the maximum drawdown for Adani Enterprises in 2023?",
    },
    {
        "name": "get_price_range",
        "description": "Get 52-week high and low for a stock",
        "code": """def get_price_range(ticker: str, weeks: int = 52) -> dict:
    \"\"\"Get high and low prices over the last N weeks.\"\"\"
    import pandas as pd
    
    df = _load_data()
    stock_data = df[df["Ticker"] == ticker].sort_values("Date", ascending=False)
    
    if stock_data.empty:
        return {"error": f"No data for {ticker}"}
    
    # Get last N weeks of data
    cutoff_date = pd.to_datetime(stock_data.iloc[0]["Date"]) - pd.Timedelta(weeks=weeks)
    recent_data = stock_data[pd.to_datetime(stock_data["Date"]) >= cutoff_date]
    
    if recent_data.empty:
        return {"error": "Insufficient data"}
    
    high_row = recent_data.loc[recent_data["High"].idxmax()]
    low_row = recent_data.loc[recent_data["Low"].idxmin()]
    current = recent_data.iloc[0]
    
    return {
        "ticker": ticker,
        "period": f"Last {weeks} weeks",
        "current_price": float(current["Close"]),
        "high": float(high_row["High"]),
        "high_date": str(high_row["Date"]),
        "low": float(low_row["Low"]),
        "low_date": str(low_row["Date"]),
        "range": float(high_row["High"] - low_row["Low"]),
        "pct_from_high": float((current["Close"] - high_row["High"]) / high_row["High"] * 100),
        "pct_from_low": float((current["Close"] - low_row["Low"]) / low_row["Low"] * 100)
    }""",
        "test_query": "What is the 52-week range for Maruti Suzuki?",
    },
    {
        "name": "compare_ytd_performance",
        "description": "Compare year-to-date performance of multiple stocks",
        "code": """def compare_ytd_performance(tickers: list, year: int) -> dict:
    \"\"\"Compare YTD performance of stocks.\"\"\"
    import pandas as pd
    
    df = _load_data()
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])
    
    results = {}
    for ticker in tickers:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"].dt.year == year)].sort_values("Date")
        if not stock_data.empty and len(stock_data) >= 2:
            start_price = float(stock_data.iloc[0]["Close"])
            end_price = float(stock_data.iloc[-1]["Close"])
            return_pct = ((end_price - start_price) / start_price) * 100
            results[ticker] = {
                "start_price": start_price,
                "end_price": end_price,
                "ytd_return_pct": return_pct
            }
    
    if results:
        sorted_tickers = sorted(results.keys(), key=lambda x: results[x]["ytd_return_pct"], reverse=True)
        best = sorted_tickers[0]
        worst = sorted_tickers[-1]
    else:
        best, worst = None, None
    
    return {
        "year": year,
        "performances": results,
        "best_performer": best,
        "worst_performer": worst
    }""",
        "test_query": "Compare YTD performance of banking stocks in 2024",
    },
    {
        "name": "calculate_rsi",
        "description": "Calculate Relative Strength Index (RSI) indicator",
        "code": """def calculate_rsi(ticker: str, period: int = 14, start_date: str = None, end_date: str = None) -> dict:
    \"\"\"Calculate RSI technical indicator.\"\"\"
    import pandas as pd
    
    df = _load_data()
    
    if start_date and end_date:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    else:
        stock_data = df[df["Ticker"] == ticker].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < period + 1:
        return {"error": "Insufficient data for RSI calculation"}
    
    # Calculate price changes
    delta = stock_data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    current_rsi = float(rsi.iloc[-1])
    
    # Interpretation
    if current_rsi > 70:
        signal = "Overbought"
    elif current_rsi < 30:
        signal = "Oversold"
    else:
        signal = "Neutral"
    
    return {
        "ticker": ticker,
        "rsi_period": period,
        "current_rsi": current_rsi,
        "signal": signal,
        "date": str(stock_data.iloc[-1]["Date"])
    }""",
        "test_query": "What is the RSI for ITC?",
    },
    {
        "name": "get_quarterly_performance",
        "description": "Analyze quarterly performance for a stock",
        "code": """def get_quarterly_performance(ticker: str, year: int) -> dict:
    \"\"\"Get quarterly returns for a stock.\"\"\"
    import pandas as pd
    
    df = _load_data()
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])
        
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"].dt.year == year)].copy()
    
    if stock_data.empty:
        return {"error": f"No data for {ticker} in {year}"}
    
    stock_data["Quarter"] = stock_data["Date"].dt.quarter
    
    quarterly = {}
    for q in [1, 2, 3, 4]:
        q_data = stock_data[stock_data["Quarter"] == q]
        if not q_data.empty and len(q_data) >= 2:
            start = float(q_data.iloc[0]["Close"])
            end = float(q_data.iloc[-1]["Close"])
            quarterly[f"Q{q}"] = {
                "return_pct": ((end - start) / start) * 100,
                "start_price": start,
                "end_price": end
            }
    
    return {
        "ticker": ticker,
        "year": year,
        "quarterly_performance": quarterly
    }""",
        "test_query": "What was Tata Steel's quarterly performance in 2024?",
    },
    {
        "name": "detect_support_resistance",
        "description": "Identify support and resistance levels based on price history",
        "code": """def detect_support_resistance(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Detect support and resistance levels.\"\"\"
    import numpy as np
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 20:
        return {"error": "Insufficient data"}
    
    # Simple support/resistance detection using percentiles
    highs = stock_data["High"].values
    lows = stock_data["Low"].values
    
    resistance_levels = [
        float(np.percentile(highs, 90)),
        float(np.percentile(highs, 95)),
        float(highs.max())
    ]
    
    support_levels = [
        float(np.percentile(lows, 10)),
        float(np.percentile(lows, 5)),
        float(lows.min())
    ]
    
    current_price = float(stock_data.iloc[-1]["Close"])
    
    return {
        "ticker": ticker,
        "current_price": current_price,
        "resistance_levels": sorted(set(resistance_levels), reverse=True),
        "support_levels": sorted(set(support_levels), reverse=True)
    }""",
        "test_query": "What are the support and resistance levels for Sun Pharma?",
    },
    {
        "name": "calculate_beta",
        "description": "Calculate beta (market sensitivity) relative to benchmark",
        "code": """def calculate_beta(ticker: str, benchmark: str, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate stock beta relative to a benchmark.\"\"\"
    import numpy as np
    
    df = _load_data()
    
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    bench_data = df[(df["Ticker"] == benchmark) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    # Merge on date
    merged = stock_data[["Date", "Close"]].merge(bench_data[["Date", "Close"]], on="Date", suffixes=("_stock", "_bench"))
    
    if len(merged) < 30:
        return {"error": "Insufficient overlapping data"}
    
    # Calculate returns
    stock_returns = merged["Close_stock"].pct_change().dropna()
    bench_returns = merged["Close_bench"].pct_change().dropna()
    
    # Beta = Covariance(stock, benchmark) / Variance(benchmark)
    covariance = float(np.cov(stock_returns, bench_returns)[0][1])
    variance = float(np.var(bench_returns))
    beta = covariance / variance
    
    interpretation = "High volatility" if beta > 1.2 else "Low volatility" if beta < 0.8 else "Similar to market"
    
    return {
        "ticker": ticker,
        "benchmark": benchmark,
        "beta": beta,
        "interpretation": interpretation,
        "data_points": len(merged)
    }""",
        "test_query": "What is the beta of Wipro relative to TCS?",
    },
    {
        "name": "find_consecutive_gains",
        "description": "Find longest streak of consecutive gaining days",
        "code": """def find_consecutive_gains(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Find longest consecutive gaining streak.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 2:
        return {"error": "Insufficient data"}
    
    stock_data["Daily_Change"] = stock_data["Close"].diff()
    stock_data["Is_Gain"] = stock_data["Daily_Change"] > 0
    
    max_streak = 0
    current_streak = 0
    streak_start_idx = 0
    max_streak_start_idx = 0
    
    for i, is_gain in enumerate(stock_data["Is_Gain"]):
        if is_gain:
            if current_streak == 0:
                streak_start_idx = i
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
                max_streak_start_idx = streak_start_idx
        else:
            current_streak = 0
    
    if max_streak > 0:
        start_date_streak = str(stock_data.iloc[max_streak_start_idx]["Date"])
        end_date_streak = str(stock_data.iloc[max_streak_start_idx + max_streak - 1]["Date"])
    else:
        start_date_streak = end_date_streak = None
    
    return {
        "ticker": ticker,
        "longest_gain_streak": max_streak,
        "streak_start_date": start_date_streak,
        "streak_end_date": end_date_streak
    }""",
        "test_query": "What was the longest gaining streak for Bharti Airtel in 2024?",
    },
    {
        "name": "find_consecutive_losses",
        "description": "Find longest streak of consecutive losing days",
        "code": """def find_consecutive_losses(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Find longest consecutive losing streak.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 2:
        return {"error": "Insufficient data"}
    
    stock_data["Daily_Change"] = stock_data["Close"].diff()
    stock_data["Is_Loss"] = stock_data["Daily_Change"] < 0
    
    max_streak = 0
    current_streak = 0
    streak_start_idx = 0
    max_streak_start_idx = 0
    
    for i, is_loss in enumerate(stock_data["Is_Loss"]):
        if is_loss:
            if current_streak == 0:
                streak_start_idx = i
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
                max_streak_start_idx = streak_start_idx
        else:
            current_streak = 0
    
    if max_streak > 0:
        start_date_streak = str(stock_data.iloc[max_streak_start_idx]["Date"])
        end_date_streak = str(stock_data.iloc[max_streak_start_idx + max_streak - 1]["Date"])
    else:
        start_date_streak = end_date_streak = None
    
    return {
        "ticker": ticker,
        "longest_loss_streak": max_streak,
        "streak_start_date": start_date_streak,
        "streak_end_date": end_date_streak
    }""",
        "test_query": "What was the longest losing streak for LT in 2023?",
    },
    {
        "name": "calculate_sharpe_ratio",
        "description": "Calculate Sharpe ratio (risk-adjusted return)",
        "code": """def calculate_sharpe_ratio(ticker: str, start_date: str, end_date: str, risk_free_rate: float = 0.06) -> dict:
    \"\"\"Calculate Sharpe ratio for risk-adjusted returns.\"\"\"
    import numpy as np
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 30:
        return {"error": "Insufficient data"}
    
    # Calculate daily returns
    returns = stock_data["Close"].pct_change().dropna()
    
    # Annualize
    annual_return = float(returns.mean() * 252)
    annual_volatility = float(returns.std() * np.sqrt(252))
    
    # Sharpe ratio = (Return - Risk_free_rate) / Volatility
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
    
    interpretation = "Excellent" if sharpe_ratio > 2 else "Good" if sharpe_ratio > 1 else "Fair" if sharpe_ratio > 0 else "Poor"
    
    return {
        "ticker": ticker,
        "sharpe_ratio": float(sharpe_ratio),
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "risk_free_rate": risk_free_rate,
        "interpretation": interpretation
    }""",
        "test_query": "What is the Sharpe ratio for ICICI Bank in 2024?",
    },
    {
        "name": "get_intraday_range",
        "description": "Analyze average intraday price range (High - Low)",
        "code": """def get_intraday_range(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate average intraday range and volatility.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    stock_data["Intraday_Range"] = stock_data["High"] - stock_data["Low"]
    stock_data["Intraday_Range_Pct"] = (stock_data["Intraday_Range"] / stock_data["Open"]) * 100
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "avg_intraday_range": float(stock_data["Intraday_Range"].mean()),
        "avg_intraday_range_pct": float(stock_data["Intraday_Range_Pct"].mean()),
        "max_intraday_range": float(stock_data["Intraday_Range"].max()),
        "max_range_date": str(stock_data.loc[stock_data["Intraday_Range"].idxmax(), "Date"])
    }""",
        "test_query": "What is the average intraday range for Dr. Reddy's in 2024?",
    },
    {
        "name": "compare_opening_vs_closing",
        "description": "Analyze how often stock closes above its opening price",
        "code": """def compare_opening_vs_closing(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Analyze opening vs closing price patterns.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    stock_data["Closed_Higher"] = stock_data["Close"] > stock_data["Open"]
    
    closes_higher = int(stock_data["Closed_Higher"].sum())
    total_days = len(stock_data)
    win_rate = (closes_higher / total_days) * 100
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "total_trading_days": total_days,
        "days_closed_higher": closes_higher,
        "days_closed_lower": total_days - closes_higher,
        "win_rate_pct": float(win_rate)
    }""",
        "test_query": "How often does SBI close higher than its opening in 2024?",
    },
    {
        "name": "get_price_momentum",
        "description": "Calculate price momentum over different timeframes",
        "code": """def get_price_momentum(ticker: str) -> dict:
    \"\"\"Calculate momentum over 1 week, 1 month, 3 months, 6 months.\"\"\"
    import pandas as pd
    
    df = _load_data()
    stock_data = df[df["Ticker"] == ticker].sort_values("Date", ascending=False)
    
    if stock_data.empty or len(stock_data) < 126:  # ~6 months of trading days
        return {"error": "Insufficient data"}
    
    current_price = float(stock_data.iloc[0]["Close"])
    current_date = str(stock_data.iloc[0]["Date"])
    
    # Calculate returns for different periods
    periods = {
        "1_week": 5,
        "1_month": 21,
        "3_months": 63,
        "6_months": 126
    }
    
    momentum = {}
    for period_name, days in periods.items():
        if len(stock_data) > days:
            past_price = float(stock_data.iloc[days]["Close"])
            return_pct = ((current_price - past_price) / past_price) * 100
            momentum[period_name] = {
                "return_pct": return_pct,
                "past_price": past_price
            }
    
    return {
        "ticker": ticker,
        "current_price": current_price,
        "as_of_date": current_date,
        "momentum": momentum
    }""",
        "test_query": "What is the price momentum for Hindustan Unilever?",
    },
    {
        "name": "analyze_gap_ups_downs",
        "description": "Find and analyze price gaps (gap up/down openings)",
        "code": """def analyze_gap_ups_downs(ticker: str, start_date: str, end_date: str, min_gap_pct: float = 2.0) -> dict:
    \"\"\"Find significant gap ups and gap downs.\"\"\"
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 2:
        return {"error": "Insufficient data"}
    
    gaps = []
    for i in range(1, len(stock_data)):
        prev_close = stock_data.iloc[i-1]["Close"]
        curr_open = stock_data.iloc[i]["Open"]
        gap_pct = ((curr_open - prev_close) / prev_close) * 100
        
        if abs(gap_pct) >= min_gap_pct:
            gaps.append({
                "date": str(stock_data.iloc[i]["Date"]),
                "gap_pct": float(gap_pct),
                "type": "Gap Up" if gap_pct > 0 else "Gap Down",
                "prev_close": float(prev_close),
                "open": float(curr_open)
            })
    
    gap_ups = [g for g in gaps if g["gap_pct"] > 0]
    gap_downs = [g for g in gaps if g["gap_pct"] < 0]
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "min_gap_threshold_pct": min_gap_pct,
        "total_gaps": len(gaps),
        "gap_ups": len(gap_ups),
        "gap_downs": len(gap_downs),
        "significant_gaps": sorted(gaps, key=lambda x: abs(x["gap_pct"]), reverse=True)[:10]
    }""",
        "test_query": "Find gap ups and gap downs for Asian Paints in 2024",
    },
    {
        "name": "calculate_average_true_range",
        "description": "Calculate Average True Range (ATR) volatility indicator",
        "code": """def calculate_average_true_range(ticker: str, period: int = 14, start_date: str = None, end_date: str = None) -> dict:
    \"\"\"Calculate ATR for measuring volatility.\"\"\"
    import numpy as np
    
    df = _load_data()
    
    if start_date and end_date:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    else:
        stock_data = df[df["Ticker"] == ticker].sort_values("Date").tail(100)
    
    if stock_data.empty or len(stock_data) < period + 1:
        return {"error": "Insufficient data"}
    
    # Calculate True Range
    high_low = stock_data["High"] - stock_data["Low"]
    high_close = np.abs(stock_data["High"] - stock_data["Close"].shift())
    low_close = np.abs(stock_data["Low"] - stock_data["Close"].shift())
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    
    current_atr = float(atr.iloc[-1])
    current_price = float(stock_data.iloc[-1]["Close"])
    atr_pct = (current_atr / current_price) * 100
    
    return {
        "ticker": ticker,
        "atr_period": period,
        "current_atr": current_atr,
        "current_price": current_price,
        "atr_percentage": atr_pct,
        "date": str(stock_data.iloc[-1]["Date"])
    }""",
        "test_query": "What is the ATR for Bajaj Finance?",
    },
    {
        "name": "find_all_time_high",
        "description": "Find if stock is at all-time high and historical ATH",
        "code": """def find_all_time_high(ticker: str) -> dict:
    \"\"\"Find all-time high price and compare to current.\"\"\"
    df = _load_data()
    stock_data = df[df["Ticker"] == ticker].sort_values("Date")
    
    if stock_data.empty:
        return {"error": f"No data for {ticker}"}
    
    ath_row = stock_data.loc[stock_data["High"].idxmax()]
    current = stock_data.iloc[-1]
    
    ath_price = float(ath_row["High"])
    current_price = float(current["Close"])
    pct_from_ath = ((current_price - ath_price) / ath_price) * 100
    
    is_at_ath = abs(pct_from_ath) < 1.0  # Within 1% of ATH
    
    return {
        "ticker": ticker,
        "current_price": current_price,
        "current_date": str(current["Date"]),
        "all_time_high": ath_price,
        "ath_date": str(ath_row["Date"]),
        "pct_from_ath": pct_from_ath,
        "is_at_ath": is_at_ath
    }""",
        "test_query": "Is Reliance at all-time high?",
    },
    {
        "name": "compare_risk_return",
        "description": "Compare risk-return profile of multiple stocks",
        "code": """def compare_risk_return(tickers: list, start_date: str, end_date: str) -> dict:
    \"\"\"Compare risk (volatility) vs return for multiple stocks.\"\"\"
    import matplotlib.pyplot as plt
    import numpy as np
    from pathlib import Path
    
    df = _load_data()
    
    results = {}
    for ticker in tickers:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
        if not stock_data.empty and len(stock_data) >= 30:
            returns = stock_data["Close"].pct_change().dropna()
            annual_return = float(returns.mean() * 252)
            annual_vol = float(returns.std() * np.sqrt(252))
            
            total_return = float(((stock_data.iloc[-1]["Close"] - stock_data.iloc[0]["Close"]) / stock_data.iloc[0]["Close"]) * 100)
            
            results[ticker] = {
                "return": annual_return * 100,
                "volatility": annual_vol * 100,
                "total_return_pct": total_return
            }
    
    if not results:
        return {"error": "No data available"}
    
    # Plot risk-return scatter
    fig, ax = plt.subplots(figsize=(12, 8))
    for ticker, data in results.items():
        ax.scatter(data["volatility"], data["return"], s=200, alpha=0.6, label=ticker)
        ax.annotate(ticker.replace(".NS", ""), (data["volatility"], data["return"]), 
                   xytext=(5, 5), textcoords='offset points')
    
    ax.set_xlabel("Risk (Annualized Volatility %)")
    ax.set_ylabel("Return (Annualized %)")
    ax.set_title(f"Risk-Return Profile ({start_date} to {end_date})")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"risk_return_comparison_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return {
        "period": f"{start_date} to {end_date}",
        "stocks": results,
        "chart_path": str(chart_path)
    }""",
        "test_query": "Compare risk-return profile of all banking stocks in 2024",
    },
    {
        "name": "calculate_exponential_moving_average",
        "description": "Calculate EMA (Exponential Moving Average)",
        "code": """def calculate_exponential_moving_average(ticker: str, span: int, start_date: str, end_date: str) -> dict:
    \"\"\"Calculate EMA and compare with current price.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < span:
        return {"error": "Insufficient data"}
    
    stock_data["EMA"] = stock_data["Close"].ewm(span=span, adjust=False).mean()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(stock_data["Date"], stock_data["Close"], label="Close Price", linewidth=2)
    ax.plot(stock_data["Date"], stock_data["EMA"], label=f"{span}-day EMA", linewidth=2, linestyle='--')
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (₹)")
    ax.set_title(f"{ticker} with {span}-day EMA")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{ticker.replace('.', '_')}_ema_{span}_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    current_price = float(stock_data.iloc[-1]["Close"])
    current_ema = float(stock_data.iloc[-1]["EMA"])
    
    signal = "Bullish" if current_price > current_ema else "Bearish"
    
    return {
        "ticker": ticker,
        "ema_period": span,
        "current_price": current_price,
        "current_ema": current_ema,
        "signal": signal,
        "chart_path": str(chart_path)
    }""",
        "test_query": "Show 20-day EMA for Tata Motors in 2024",
    },
    {
        "name": "get_weekly_summary",
        "description": "Get weekly OHLC summary for a stock",
        "code": """def get_weekly_summary(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Aggregate daily data into weekly summary.\"\"\"
    import pandas as pd
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    stock_data["Date"] = pd.to_datetime(stock_data["Date"])
    stock_data.set_index("Date", inplace=True)
    
    # Resample to weekly
    weekly = stock_data.resample('W').agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    }).dropna()
    
    weekly_data = []
    for date, row in weekly.iterrows():
        weekly_data.append({
            "week_ending": str(date.date()),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"])
        })
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "total_weeks": len(weekly_data),
        "weekly_data": weekly_data
    }""",
        "test_query": "Get weekly summary for Infosys in November 2024",
    },
    {
        "name": "find_pivot_points",
        "description": "Calculate pivot points for support/resistance trading",
        "code": """def find_pivot_points(ticker: str) -> dict:
    \"\"\"Calculate pivot points based on recent price action.\"\"\"
    df = _load_data()
    stock_data = df[df["Ticker"] == ticker].sort_values("Date", ascending=False)
    
    if stock_data.empty:
        return {"error": f"No data for {ticker}"}
    
    # Use yesterday's data for pivot calculation
    yesterday = stock_data.iloc[1] if len(stock_data) > 1 else stock_data.iloc[0]
    
    high = float(yesterday["High"])
    low = float(yesterday["Low"])
    close = float(yesterday["Close"])
    
    # Calculate pivot point
    pivot = (high + low + close) / 3
    
    # Calculate support and resistance levels
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    
    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)
    
    current_price = float(stock_data.iloc[0]["Close"])
    
    return {
        "ticker": ticker,
        "current_price": current_price,
        "pivot_point": float(pivot),
        "resistance_1": float(r1),
        "resistance_2": float(r2),
        "resistance_3": float(r3),
        "support_1": float(s1),
        "support_2": float(s2),
        "support_3": float(s3),
        "based_on_date": str(yesterday["Date"])
    }""",
        "test_query": "What are the pivot points for HDFC Bank today?",
    },
    {
        "name": "analyze_weekend_effect",
        "description": "Analyze Friday close vs Monday open patterns",
        "code": """def analyze_weekend_effect(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Analyze price behavior around weekends.\"\"\"
    import pandas as pd
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    stock_data["Date"] = pd.to_datetime(stock_data["Date"])
    stock_data["DayOfWeek"] = stock_data["Date"].dt.dayofweek
    
    # Find Fridays and following Mondays
    fridays = stock_data[stock_data["DayOfWeek"] == 4].copy()
    mondays = stock_data[stock_data["DayOfWeek"] == 0].copy()
    
    weekend_gaps = []
    for _, friday in fridays.iterrows():
        monday = mondays[mondays["Date"] > friday["Date"]].head(1)
        if not monday.empty:
            monday_row = monday.iloc[0]
            gap = ((monday_row["Open"] - friday["Close"]) / friday["Close"]) * 100
            weekend_gaps.append(float(gap))
    
    if weekend_gaps:
        avg_gap = sum(weekend_gaps) / len(weekend_gaps)
        positive_gaps = len([g for g in weekend_gaps if g > 0])
        negative_gaps = len([g for g in weekend_gaps if g < 0])
    else:
        avg_gap = positive_gaps = negative_gaps = 0
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "total_weekends_analyzed": len(weekend_gaps),
        "average_weekend_gap_pct": float(avg_gap),
        "positive_gaps": positive_gaps,
        "negative_gaps": negative_gaps
    }""",
        "test_query": "Analyze weekend effect for SBI in 2024",
    },
    {
        "name": "calculate_bollinger_bands",
        "description": "Calculate Bollinger Bands for volatility analysis",
        "code": """def calculate_bollinger_bands(ticker: str, period: int = 20, std_dev: int = 2, start_date: str = None, end_date: str = None) -> dict:
    \"\"\"Calculate Bollinger Bands and plot them.\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    
    if start_date and end_date:
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
    else:
        stock_data = df[df["Ticker"] == ticker].sort_values("Date").tail(100)
    
    if stock_data.empty or len(stock_data) < period:
        return {"error": "Insufficient data"}
    
    # Calculate Bollinger Bands
    stock_data["SMA"] = stock_data["Close"].rolling(window=period).mean()
    stock_data["STD"] = stock_data["Close"].rolling(window=period).std()
    stock_data["Upper_Band"] = stock_data["SMA"] + (std_dev * stock_data["STD"])
    stock_data["Lower_Band"] = stock_data["SMA"] - (std_dev * stock_data["STD"])
    
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(stock_data["Date"], stock_data["Close"], label="Close Price", linewidth=2, color='black')
    ax.plot(stock_data["Date"], stock_data["SMA"], label=f"{period}-day SMA", linewidth=1, linestyle='--', color='blue')
    ax.plot(stock_data["Date"], stock_data["Upper_Band"], label="Upper Band", linewidth=1, linestyle=':', color='red')
    ax.plot(stock_data["Date"], stock_data["Lower_Band"], label="Lower Band", linewidth=1, linestyle=':', color='green')
    ax.fill_between(stock_data["Date"], stock_data["Lower_Band"], stock_data["Upper_Band"], alpha=0.1)
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (₹)")
    ax.set_title(f"{ticker} Bollinger Bands ({period} period, {std_dev} std dev)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"{ticker.replace('.', '_')}_bollinger_{period}_{std_dev}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    current = stock_data.iloc[-1]
    current_price = float(current["Close"])
    upper = float(current["Upper_Band"])
    lower = float(current["Lower_Band"])
    sma = float(current["SMA"])
    
    # Determine position
    if current_price > upper:
        position = "Above upper band (overbought)"
    elif current_price < lower:
        position = "Below lower band (oversold)"
    else:
        position = "Within bands"
    
    return {
        "ticker": ticker,
        "current_price": current_price,
        "sma": sma,
        "upper_band": upper,
        "lower_band": lower,
        "position": position,
        "chart_path": str(chart_path)
    }""",
        "test_query": "Show Bollinger Bands for LT",
    },
    {
        "name": "compare_sector_leaders",
        "description": "Compare market leaders from different sectors",
        "code": """def compare_sector_leaders(sector_leaders: dict, start_date: str, end_date: str) -> dict:
    \"\"\"Compare sector leaders (dict of sector: ticker).\"\"\"
    import matplotlib.pyplot as plt
    from pathlib import Path
    
    df = _load_data()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    results = {}
    
    for sector, ticker in sector_leaders.items():
        stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].sort_values("Date")
        if not stock_data.empty and len(stock_data) >= 2:
            # Normalize
            normalized = (stock_data["Close"] / stock_data["Close"].iloc[0]) * 100
            ax.plot(stock_data["Date"], normalized, label=f"{sector} ({ticker})", linewidth=2)
            
            final_return = float(normalized.iloc[-1] - 100)
            results[sector] = {
                "ticker": ticker,
                "return_pct": final_return
            }
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Value (Base 100)")
    ax.set_title(f"Sector Leaders Comparison ({start_date} to {end_date})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = settings.charts_dir / f"sector_leaders_{start_date}_{end_date}.png"
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    return {
        "period": f"{start_date} to {end_date}",
        "sectors": results,
        "chart_path": str(chart_path)
    }""",
        "test_query": "Compare IT, Banking, and Pharma sector leaders in 2024",
    },
    {
        "name": "get_dividend_dates_estimate",
        "description": "Estimate potential dividend announcement patterns (based on historical price spikes)",
        "code": """def get_dividend_dates_estimate(ticker: str, year: int) -> dict:
    \"\"\"Identify potential dividend-related price movements.\"\"\"
    import pandas as pd
    
    df = _load_data()
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])
        
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"].dt.year == year)].sort_values("Date")
    
    if stock_data.empty or len(stock_data) < 10:
        return {"error": "Insufficient data"}
    
    # Find days with unusually high volume (possible dividend announcement days)
    avg_volume = stock_data["Volume"].mean()
    std_volume = stock_data["Volume"].std()
    
    high_volume_days = stock_data[stock_data["Volume"] > (avg_volume + 2 * std_volume)]
    
    potential_events = []
    for _, row in high_volume_days.iterrows():
        potential_events.append({
            "date": str(row["Date"]),
            "volume": int(row["Volume"]),
            "price_change_pct": float(((row["Close"] - row["Open"]) / row["Open"]) * 100),
            "note": "High volume day - possible corporate action"
        })
    
    return {
        "ticker": ticker,
        "year": year,
        "average_volume": int(avg_volume),
        "high_volume_threshold": int(avg_volume + 2 * std_volume),
        "potential_dividend_dates": potential_events
    }""",
        "test_query": "When might HDFC Bank announce dividends in 2024?",
    },
    {
        "name": "calculate_price_to_high_low_ratio",
        "description": "Calculate where current price stands in yearly range",
        "code": """def calculate_price_to_high_low_ratio(ticker: str, year: int) -> dict:
    \"\"\"Calculate price position in year's high-low range.\"\"\"
    import pandas as pd
    
    df = _load_data()
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])
        
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"].dt.year == year)]
    
    if stock_data.empty:
        return {"error": f"No data for {ticker} in {year}"}
    
    yearly_high = float(stock_data["High"].max())
    yearly_low = float(stock_data["Low"].min())
    current_price = float(stock_data.sort_values("Date", ascending=False).iloc[0]["Close"])
    
    # Calculate position in range (0 = at low, 100 = at high)
    range_width = yearly_high - yearly_low
    position_in_range = ((current_price - yearly_low) / range_width) * 100 if range_width > 0 else 50
    
    if position_in_range > 80:
        interpretation = "Near yearly high"
    elif position_in_range < 20:
        interpretation = "Near yearly low"
    else:
        interpretation = "Mid-range"
    
    return {
        "ticker": ticker,
        "year": year,
        "current_price": current_price,
        "yearly_high": yearly_high,
        "yearly_low": yearly_low,
        "position_in_range_pct": float(position_in_range),
        "interpretation": interpretation
    }""",
        "test_query": "Where is Bajaj Finance trading in its 2024 range?",
    },
    {
        "name": "find_breakout_stocks",
        "description": "Find stocks breaking out of their historical ranges",
        "code": """def find_breakout_stocks(tickers: list, lookback_days: int = 90) -> dict:
    \"\"\"Find stocks breaking above recent highs (potential breakouts).\"\"\"
    import pandas as pd
    
    df = _load_data()
    
    breakouts = []
    for ticker in tickers:
        stock_data = df[df["Ticker"] == ticker].sort_values("Date", ascending=False)
        if len(stock_data) < lookback_days + 5:
            continue
        
        current_price = float(stock_data.iloc[0]["Close"])
        historical_data = stock_data.iloc[5:lookback_days+5]  # Skip last 5 days
        historical_high = float(historical_data["High"].max())
        
        if current_price > historical_high:
            pct_above = ((current_price - historical_high) / historical_high) * 100
            breakouts.append({
                "ticker": ticker,
                "current_price": current_price,
                "historical_high": historical_high,
                "breakout_pct": float(pct_above),
                "current_date": str(stock_data.iloc[0]["Date"])
            })
    
    breakouts.sort(key=lambda x: x["breakout_pct"], reverse=True)
    
    return {
        "lookback_period_days": lookback_days,
        "total_stocks_analyzed": len(tickers),
        "breakout_count": len(breakouts),
        "breakout_stocks": breakouts
    }""",
        "test_query": "Which stocks are breaking out to new highs?",
    },
    {
        "name": "analyze_monday_effect",
        "description": "Analyze if Mondays have different returns than other days",
        "code": """def analyze_monday_effect(ticker: str, start_date: str, end_date: str) -> dict:
    \"\"\"Analyze day-of-week effect, focusing on Mondays.\"\"\"
    import pandas as pd
    
    df = _load_data()
    stock_data = df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()
    
    if stock_data.empty:
        return {"error": "No data available"}
    
    stock_data["Date"] = pd.to_datetime(stock_data["Date"])
    stock_data["DayOfWeek"] = stock_data["Date"].dt.day_name()
    stock_data["Daily_Return"] = stock_data["Close"].pct_change() * 100
    
    day_returns = stock_data.groupby("DayOfWeek")["Daily_Return"].agg(['mean', 'count']).to_dict()
    
    avg_by_day = {}
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        if day in day_returns['mean']:
            avg_by_day[day] = {
                "avg_return_pct": float(day_returns['mean'][day]),
                "occurrences": int(day_returns['count'][day])
            }
    
    return {
        "ticker": ticker,
        "period": f"{start_date} to {end_date}",
        "average_returns_by_day": avg_by_day
    }""",
        "test_query": "Does Infosys have a Monday effect?",
    },
]


def seed_interface_library():
    """Seed the interface library with pre-built functions."""
    logger.info("Starting interface library seeding...")
    
    # Clear existing library
    interface_library.clear()
    logger.info("Cleared existing library")
    
    # Add all seed interfaces
    for interface in SEED_INTERFACES:
        interface_library.add(
            name=interface["name"],
            code=interface["code"],
            description=interface["description"],
            test_query=interface["test_query"]
        )
        logger.info(f"Added interface: {interface['name']}")
    
    # Rebuild FAISS index
    from services.agent_service import agent_service
    agent_service._rebuild_index()
    
    logger.info(f"✅ Successfully seeded {len(SEED_INTERFACES)} interfaces")
    logger.info(f"Total interfaces in library: {len(interface_library.list_all())}")
    
    # Print summary
    print("\n" + "="*70)
    print("COMPREHENSIVE INTERFACE LIBRARY SEEDED SUCCESSFULLY")
    print("="*70)
    print(f"\n{len(SEED_INTERFACES)} Pre-Built Stock Analysis Interfaces:\n")
    
    categories = {
        "Price & Fundamentals": list(range(0, 10)),
        "Technical Analysis": list(range(10, 20)),
        "Comparative Analysis": list(range(20, 30)),
        "Risk & Volatility": list(range(30, 40)),
        "Advanced Patterns": list(range(40, 50))
    }
    
    for category, indices in categories.items():
        print(f"\n{category}:")
        for i in indices:
            if i < len(SEED_INTERFACES):
                interface = SEED_INTERFACES[i]
                print(f"  {i+1:2d}. {interface['name']}")
    
    print("\n" + "="*70)
    print(f"Total: {len(SEED_INTERFACES)} interfaces ready for instant reuse!")
    print("Zero cold-start delays • 100% reuse rate for matching queries")
    print("="*70 + "\n")


if __name__ == "__main__":
    seed_interface_library()
