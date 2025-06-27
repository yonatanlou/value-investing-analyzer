# Value Investing Radar

A Python-based automated pipeline that analyzes Reddit's r/ValueInvesting subreddit to identify and rank value investing opportunities using fundamental analysis and DCF calculations.

## 🎯 Overview

This tool automates a weekly pipeline that:

1. **Scrapes** the past-7-days content from r/ValueInvesting
2. **Identifies** the most-discussed tickers (with noise filtering and weighting)
3. **Runs** fundamental "value-investing" analysis on each ticker
4. **Ranks & recommends** the resulting stocks (Buy / Hold / Avoid)
5. **Outputs** a tidy CSV + console summary

## 🏗️ Architecture

```
┌─────────────────┐
│  config.yaml    │  ← API keys, scoring weights, run options
└────────┬────────┘
         │
┌────────▼────────┐
│ RedditScraper   │  ← PRAW or Pushshift fallback
└────────┬────────┘
         │ raw posts (JSON)
┌────────▼────────┐
│ TickerExtractor │  ← NLP / regex + ticker-list validation
└────────┬────────┘
         │ top-N tickers
┌────────▼────────┐
│ ValueAnalyzer   │  ← yfinance fundamentals + DCF
└────────┬────────┘
         │ scored tickers
┌────────▼────────┐
│ Ranker          │  ← weighted score → Buy / Hold / Avoid
└────────┬────────┘
         │
┌────────▼────────┐
│ OutputWriter    │  ← CSV + pretty console table
└─────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd value-investing-analyzer

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

#### Option A: Environment Variables (Recommended)

Create a `.env` file in the project root:

```bash
# Copy the example file
cp env.example .env

# Edit the .env file with your credentials
nano .env
```

Add your Reddit API credentials to the `.env` file:

```bash
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

**Security Note:** The `.env` file is automatically ignored by git to keep your credentials secure. Never commit your actual API credentials to version control.

#### Option B: Direct Configuration

Alternatively, you can edit `config.yaml` directly:

```yaml
reddit:
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  user_agent: "value_radar/0.1 by yourname"
```

**Getting Reddit API Credentials:**
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as the app type
4. Note your `client_id` and `client_secret`

### 3. Run Analysis

```bash
# Run with default config
python -m src.main

# Run with custom config
python -m src.main --config my_config.yaml

# Dry run (no file output)
python -m src.main --dry-run
```

## 📊 Sample Output

### Console Output
```
Value Investing Radar Report
Generated: 2024-01-15 14:30:25

Summary Statistics:
Total Stocks Analyzed    15
BUY Recommendations      3
HOLD Recommendations     8
AVOID Recommendations    4
Average Composite Score  62.3
Average Margin of Safety 8.7%

Top Stock Recommendations:
┌─────┬────────┬──────┬────────┬──────────┬───────┬─────┬──────┬──────┬────────────────────────────────────────┐
│Rank │Ticker  │Rec   │Score   │Price     │MOS%   │P/E  │ROE%  │FCF%  │Rationale                               │
├─────┼────────┼──────┼────────┼──────────┼───────┼─────┼──────┼──────┼────────────────────────────────────────┤
│1    │AAPL    │BUY   │85.2    │$175.43   │25.3%  │15.2 │18.5% │8.2%  │MOS=25.3%, Strong ROE=18.5%, Low debt   │
│2    │MSFT    │BUY   │82.1    │$378.85   │22.1%  │32.1 │35.2% │6.8%  │MOS=22.1%, Strong ROE=35.2%, High growth│
│3    │JNJ     │HOLD  │68.4    │$162.34   │12.5%  │14.8 │22.1% │5.1%  │MOS=12.5%, Good ROE=22.1%, Low debt     │
└─────┴────────┴──────┴────────┴──────────┴───────┴─────┴──────┴──────┴────────────────────────────────────────┘
```

### CSV Output
The tool generates a CSV file in `reports/value_radar_YYYY-MM-DD.csv` with columns:
- ticker, recommendation, composite_score, current_price
- intrinsic_value, margin_of_safety, pe_ratio, pb_ratio
- fcf_yield, roe, revenue_cagr, debt_to_equity, dividend_yield
- quality_score, health_score, popularity_score, mention_count, rationale

## ⚙️ Configuration

### Key Configuration Options

```yaml
scraper:
  days_back: 7          # How many days back to scrape
  max_posts: 800        # Maximum posts to analyze
  subreddit: "valueinvesting"

ticker_extractor:
  top_n: 15             # Number of top tickers to analyze
  min_mentions: 2       # Minimum mentions to consider

analyzer:
  discount_rate: 0.08   # DCF discount rate
  terminal_growth: 0.02 # Terminal growth rate
  explicit_growth: 0.06 # Explicit period growth rate

ranker:
  weights:
    mos: 0.4            # Margin of safety weight
    quality: 0.3        # Quality metrics weight
    health: 0.2         # Financial health weight
    popularity: 0.1     # Reddit popularity weight
  thresholds:
    buy: 75             # Score threshold for BUY
    hold: 50            # Score threshold for HOLD
```

## 🧪 Testing

Run the test suite:

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_ticker_extractor.py

# Run with verbose output
pytest -v tests/
```

## 📁 Project Structure

```
value-investing-analyzer/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── reddit_scraper.py    # Reddit data collection
│   ├── ticker_extractor.py  # Ticker identification
│   ├── value_analyzer.py    # Fundamental analysis
│   ├── ranker.py           # Scoring and ranking
│   └── output_writer.py    # Report generation
├── tests/
│   ├── __init__.py
│   ├── test_ticker_extractor.py
│   └── test_ranker.py
├── assets/
│   ├── valid_tickers.csv    # Valid ticker symbols
│   └── ticker_map.csv       # Company name mappings
├── data/
│   └── raw/                 # Raw scraped data
├── reports/                 # Generated CSV reports
├── config.yaml             # Configuration file
├── env.example             # Environment variables template
├── .env                    # Environment variables (create from env.example)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Dependencies

- **praw**: Reddit API wrapper
- **yfinance**: Yahoo Finance data
- **pandas**: Data manipulation
- **numpy**: Numerical computations
- **rich**: Beautiful console output
- **pyyaml**: Configuration file parsing
- **requests**: HTTP requests (Pushshift fallback)

## 🚨 Rate Limiting & API Usage

- **PRAW**: Respects Reddit's 60 requests/minute limit
- **yfinance**: No API key required, but rate limited
- **Pushshift**: Used as fallback when PRAW credentials unavailable

## 📈 Value Investing Metrics

The analyzer calculates and considers:

### Fundamental Metrics
- **P/E Ratio**: Price-to-Earnings (trailing twelve months)
- **P/B Ratio**: Price-to-Book ratio
- **FCF Yield**: Free Cash Flow Yield
- **ROE**: Return on Equity
- **Revenue CAGR**: 5-year revenue compound annual growth rate
- **Debt/Equity**: Debt-to-Equity ratio
- **Dividend Yield**: Annual dividend yield

### DCF Analysis
- **Intrinsic Value**: 2-stage DCF model
- **Margin of Safety**: (Intrinsic Value - Current Price) / Intrinsic Value
- **Growth Assumptions**: 5-year explicit + terminal growth

### Scoring Components
- **Quality Score**: Based on ROE, growth, and debt levels
- **Health Score**: Based on debt, FCF, and dividend metrics
- **Popularity Score**: Reddit mention frequency and engagement

## 🔄 Automation

### Weekly Cron Job
Add to your crontab for weekly runs:

```bash
# Edit crontab
crontab -e

# Add weekly run (every Sunday at 9 AM)
0 9 * * 0 cd /path/to/value-investing-analyzer && python -m src.main
```

### Docker (Future Enhancement)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "src.main"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. It does not constitute financial advice. Always do your own research and consult with a financial advisor before making investment decisions.

## 🔮 Future Enhancements

- Sentiment analysis (VADER or FinBERT) to weight mentions
- Parallel async scraping with `asyncpraw` for speed
- Plug-in alternative data sources (Morningstar, SEC filings)
- Dockerfile & GitHub Actions CI
- Export to Google Sheets or Notion
- Web dashboard for results visualization
- Email notifications for new BUY recommendations 