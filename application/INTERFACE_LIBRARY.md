# Comprehensive Interface Library - 46 Pre-Built Stock Analysis Functions

## 🚀 Overview

This interface library contains 46 pre-built, production-ready stock analysis functions that enable **instant query responses** without LLM code generation. The Interface Agent can now reuse these functions for matching queries, dramatically reducing latency and API costs.

## 📊 Interface Categories

### 1. Price & Fundamentals (10 interfaces)
Basic price queries and fundamental metrics

1. **get_current_price** - Get the most recent closing price for a stock ticker
2. **compare_two_stocks** - Compare price trends of two stocks over a time period with a chart
3. **plot_stock_trend** - Plot the price trend of a single stock over a date range
4. **get_stock_statistics** - Calculate statistical summary (mean, std, min, max) for a stock
5. **calculate_moving_average** - Calculate and plot moving average for a stock
6. **compare_multiple_stocks** - Compare 3 or more stocks on the same chart
7. **get_yearly_high_low** - Get the highest and lowest prices for a stock in a given year
8. **calculate_stock_volatility** - Calculate volatility (standard deviation of returns) for a stock
9. **get_average_volume** - Calculate average trading volume for a stock
10. **find_best_performing_stock** - Find the best performing stock from a list in a time period

### 2. Technical Analysis (10 interfaces)
Chart patterns, indicators, and technical signals

11. **get_stock_price_on_date** - Get stock price on a specific date
12. **calculate_stock_return** - Calculate percentage return between two dates
13. **plot_candlestick_chart** - Create a candlestick chart for stock OHLC data
14. **compare_sector_performance** - Compare performance of stocks from the same sector
15. **get_monthly_returns** - Calculate monthly returns for a stock
16. **calculate_correlation** - Calculate price correlation between two stocks
17. **find_biggest_gainers** - Find stocks with highest single-day gains
18. **find_biggest_losers** - Find stocks with highest single-day losses
19. **plot_volume_analysis** - Plot volume alongside price to identify volume spikes
20. **calculate_drawdown** - Calculate maximum drawdown (peak to trough decline)

### 3. Comparative Analysis (10 interfaces)
Multi-stock comparisons and relative performance

21. **get_price_range** - Get 52-week high and low for a stock
22. **compare_ytd_performance** - Compare year-to-date performance of multiple stocks
23. **calculate_rsi** - Calculate Relative Strength Index (RSI) indicator
24. **get_quarterly_performance** - Analyze quarterly performance for a stock
25. **detect_support_resistance** - Identify support and resistance levels based on price history
26. **calculate_beta** - Calculate beta (market sensitivity) relative to benchmark
27. **find_consecutive_gains** - Find longest streak of consecutive gaining days
28. **find_consecutive_losses** - Find longest streak of consecutive losing days
29. **calculate_sharpe_ratio** - Calculate Sharpe ratio (risk-adjusted return)
30. **get_intraday_range** - Analyze average intraday price range (High - Low)

### 4. Risk & Volatility (10 interfaces)
Risk metrics, volatility analysis, and pattern detection

31. **compare_opening_vs_closing** - Analyze how often stock closes above its opening price
32. **get_price_momentum** - Calculate price momentum over different timeframes
33. **analyze_gap_ups_downs** - Find and analyze price gaps (gap up/down openings)
34. **calculate_average_true_range** - Calculate Average True Range (ATR) volatility indicator
35. **find_all_time_high** - Find if stock is at all-time high and historical ATH
36. **compare_risk_return** - Compare risk-return profile of multiple stocks
37. **calculate_exponential_moving_average** - Calculate EMA (Exponential Moving Average)
38. **get_weekly_summary** - Get weekly OHLC summary for a stock
39. **find_pivot_points** - Calculate pivot points for support/resistance trading
40. **analyze_weekend_effect** - Analyze Friday close vs Monday open patterns

### 5. Advanced Patterns (6 interfaces)
Advanced technical patterns and market behavior analysis

41. **calculate_bollinger_bands** - Calculate Bollinger Bands for volatility analysis
42. **compare_sector_leaders** - Compare market leaders from different sectors
43. **get_dividend_dates_estimate** - Estimate potential dividend announcement patterns
44. **calculate_price_to_high_low_ratio** - Calculate where current price stands in yearly range
45. **find_breakout_stocks** - Find stocks breaking out of their historical ranges
46. **analyze_monday_effect** - Analyze if Mondays have different returns than other days

## 🎯 Benefits

### Performance Improvements
- ⚡ **Zero cold-start** - No LLM code generation needed for matching queries
- 🚀 **Instant execution** - Direct function calls instead of generate→test→execute
- 💰 **Reduced API costs** - No generation tokens for reused interfaces
- 📈 **100% reuse rate** - Perfect matches execute immediately

### Quality Assurance
- ✅ **Pre-tested code** - All interfaces validated and working
- 🎨 **Consistent visualizations** - Uniform chart styling across all plots
- 🔒 **Type safety** - Proper parameter validation
- 📊 **Rich outputs** - Structured results with charts and statistics

### Coverage
- 📈 19 major Indian stocks (NSE tickers)
- 📅 3 years of historical data (2022-2024)
- 🔢 14,022 data points
- 💹 OHLC + Volume data

## 🧪 Example Queries Covered

### Basic Queries
- "What is the current price of TCS?"
- "Show me Infosys stock trend in 2024"
- "Compare TCS and Wipro"

### Technical Analysis
- "Show 50-day moving average for Reliance"
- "What is the RSI for ITC?"
- "Calculate Bollinger Bands for HDFC Bank"

### Comparative Analysis
- "Which IT stock performed best in 2024?"
- "Compare banking stocks YTD performance"
- "Find the best performing stock from my list"

### Risk Analysis
- "What is the volatility of SBI?"
- "Calculate Sharpe ratio for ICICI Bank"
- "Show risk-return profile of pharma stocks"

### Pattern Detection
- "Find gap ups for Asian Paints"
- "Is Reliance at all-time high?"
- "Which stocks are breaking out?"

## 📊 Available Stock Tickers

- **IT Sector**: TCS.NS, INFY.NS, WIPRO.NS, HCLTECH.NS
- **Banking**: HDFCBANK.NS, ICICIBANK.NS, SBIN.NS
- **Telecom**: BHARTIARTL.NS
- **Conglomerate**: RELIANCE.NS, ITC.NS, LT.NS
- **Auto**: MARUTI.NS
- **Pharma**: SUNPHARMA.NS, DRREDDY.NS
- **Steel**: TATASTEEL.NS
- **Others**: ADANIENT.NS, BAJFINANCE.NS, ASIANPAINT.NS, HINDUNILVR.NS

## 🔄 Auto-Loading

The interface library automatically loads on application startup. If the library is empty, the system will auto-seed it with all 46 interfaces.

## 🛠️ Manual Seeding

To manually re-seed the library:

```bash
python seed_library.py
```

This will:
1. Clear the existing library
2. Add all 46 pre-built interfaces
3. Rebuild the FAISS semantic search index
4. Display a summary of loaded interfaces

## 📈 Performance Metrics

**Interface Agent (with 46 pre-built interfaces)**:
- Interface reuse rate: Up to 100% for matching queries
- Code reuse rate: 50%+ on average
- Latency: <2s for reused interfaces (vs 10-15s for generation)
- Token usage: ~500 tokens (decision only) vs ~2000+ tokens (full generation)

**General LLM (baseline)**:
- Interface reuse rate: 0% (always generates fresh code)
- Code reuse rate: 0%
- Latency: Variable (5-15s depending on complexity)
- Token usage: 1500-3000 tokens per query

## 🎓 Usage Tips

1. **Use natural language** - The semantic search will match your query to the best interface
2. **Be specific with tickers** - Use proper NSE ticker format (e.g., "TCS.NS" or just "TCS")
3. **Specify time ranges** - Most interfaces support flexible date ranges
4. **Combine interfaces** - Complex queries may use multiple interfaces via DAG execution

## 🔮 Future Enhancements

- Add more specialized interfaces (options analysis, derivatives, futures)
- Sector-specific deep analysis interfaces
- Real-time data integration
- Custom indicator builders
- Portfolio optimization interfaces
