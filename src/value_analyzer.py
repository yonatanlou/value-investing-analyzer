"""
Value analyzer module for fundamental analysis and DCF calculations.
Uses yfinance for financial data and implements value investing metrics.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

import yfinance as yf

logger = logging.getLogger(__name__)


class ValueAnalyzer:
    """Performs fundamental analysis and DCF calculations for stocks."""
    
    def __init__(self, config: Dict):
        """Initialize analyzer with configuration."""
        self.config = config
        self.analyzer_config = config.get('analyzer', {})
        
    def analyze_tickers(self, tickers: List[Tuple[str, float, int, List[str]]]) -> List[Dict]:
        """Analyze a list of tickers and return fundamental data."""
        results = []
        
        for ticker, popularity_score, mention_count, reddit_links in tickers:
            try:
                analysis = self._analyze_single_ticker(ticker, popularity_score, mention_count, reddit_links)
                if analysis:
                    results.append(analysis)
                    logger.info(f"Analyzed {ticker}: MOS={analysis.get('margin_of_safety', 0):.1f}%")
                else:
                    logger.warning(f"Could not analyze {ticker}")
                    
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")
                continue
        
        logger.info(f"Successfully analyzed {len(results)} out of {len(tickers)} tickers")
        return results
    
    def _analyze_single_ticker(self, ticker: str, popularity_score: float, mention_count: int, reddit_links: List[str]) -> Optional[Dict]:
        """Analyze a single ticker and return fundamental metrics."""
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get financial data
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            
            # Calculate fundamental metrics
            metrics = self._calculate_metrics(stock, info, financials, balance_sheet, cashflow)
            
            if not metrics:
                return None
            
            # Calculate DCF and intrinsic value
            dcf_result = self._calculate_dcf(stock, metrics)
            
            # Combine all data
            result = {
                'ticker': ticker,
                'popularity_score': popularity_score,
                'mention_count': mention_count,
                'reddit_links': reddit_links,
                **metrics,
                **dcf_result
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in single ticker analysis for {ticker}: {e}")
            return None
    
    def _calculate_metrics(self, stock, info, financials, balance_sheet, cashflow) -> Optional[Dict]:
        """Calculate fundamental value investing metrics."""
        try:
            current_price = info.get('currentPrice', 0)
            if not current_price:
                return None
            
            # Basic metrics
            pe_ratio = info.get('trailingPE', 0)
            pb_ratio = info.get('priceToBook', 0)
            debt_to_equity = info.get('debtToEquity', 0)
            dividend_yield = info.get('dividendYield', 0) or 0
            
            # Calculate FCF Yield
            fcf_yield = self._calculate_fcf_yield(stock, current_price)
            
            # Calculate ROE
            roe = self._calculate_roe(financials, balance_sheet)
            
            # Calculate Revenue CAGR
            revenue_cagr = self._calculate_revenue_cagr(financials)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(roe, revenue_cagr, debt_to_equity)
            
            # Calculate financial health score
            health_score = self._calculate_health_score(debt_to_equity, fcf_yield, dividend_yield)
            
            return {
                'current_price': current_price,
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio,
                'debt_to_equity': debt_to_equity,
                'dividend_yield': dividend_yield * 100,  # Convert to percentage
                'fcf_yield': fcf_yield,
                'roe': roe,
                'revenue_cagr': revenue_cagr,
                'quality_score': quality_score,
                'health_score': health_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return None
    
    def _calculate_fcf_yield(self, stock, current_price: float) -> float:
        """Calculate Free Cash Flow Yield."""
        try:
            cashflow = stock.cashflow
            if cashflow.empty:
                return 0
            
            # Get latest FCF
            fcf = cashflow.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cashflow.index else 0
            
            # Get market cap
            market_cap = stock.info.get('marketCap', 0)
            
            if market_cap and market_cap > 0:
                return (fcf / market_cap) * 100
            elif current_price > 0:
                # Estimate using shares outstanding
                shares = stock.info.get('sharesOutstanding', 0)
                if shares:
                    return (fcf / (shares * current_price)) * 100
            
            return 0
            
        except Exception as e:
            logger.warning(f"Error calculating FCF yield: {e}")
            return 0
    
    def _calculate_roe(self, financials, balance_sheet) -> float:
        """Calculate Return on Equity."""
        try:
            if financials.empty or balance_sheet.empty:
                return 0
            
            # Get latest net income and equity
            net_income = financials.loc['Net Income'].iloc[0] if 'Net Income' in financials.index else 0
            total_equity = balance_sheet.loc['Total Stockholder Equity'].iloc[0] if 'Total Stockholder Equity' in balance_sheet.index else 0
            
            if total_equity and total_equity > 0:
                return (net_income / total_equity) * 100
            
            return 0
            
        except Exception as e:
            logger.warning(f"Error calculating ROE: {e}")
            return 0
    
    def _calculate_revenue_cagr(self, financials) -> float:
        """Calculate 5-year Revenue CAGR."""
        try:
            if financials.empty:
                return 0
            
            revenue_row = financials.loc['Total Revenue'] if 'Total Revenue' in financials.index else None
            if revenue_row is None or len(revenue_row) < 2:
                return 0
            
            # Get revenue for last 5 years (or available years)
            years = min(5, len(revenue_row))
            if years < 2:
                return 0
            
            start_revenue = revenue_row.iloc[years - 1]
            end_revenue = revenue_row.iloc[0]
            
            if start_revenue <= 0:
                return 0
            
            cagr = ((end_revenue / start_revenue) ** (1 / (years - 1)) - 1) * 100
            return cagr
            
        except Exception as e:
            logger.warning(f"Error calculating Revenue CAGR: {e}")
            return 0
    
    def _calculate_quality_score(self, roe: float, revenue_cagr: float, debt_to_equity: float) -> float:
        """Calculate quality score based on ROE, growth, and financial health."""
        score = 0
        
        # ROE component (0-40 points)
        if roe > 15:
            score += 40
        elif roe > 10:
            score += 30
        elif roe > 5:
            score += 20
        elif roe > 0:
            score += 10
        
        # Growth component (0-30 points)
        if revenue_cagr > 10:
            score += 30
        elif revenue_cagr > 5:
            score += 20
        elif revenue_cagr > 0:
            score += 10
        
        # Debt component (0-30 points)
        if debt_to_equity < 0.5:
            score += 30
        elif debt_to_equity < 1.0:
            score += 20
        elif debt_to_equity < 2.0:
            score += 10
        
        return score
    
    def _calculate_health_score(self, debt_to_equity: float, fcf_yield: float, dividend_yield: float) -> float:
        """Calculate financial health score."""
        score = 0
        
        # Debt component (0-40 points)
        if debt_to_equity < 0.3:
            score += 40
        elif debt_to_equity < 0.7:
            score += 30
        elif debt_to_equity < 1.0:
            score += 20
        elif debt_to_equity < 2.0:
            score += 10
        
        # FCF Yield component (0-40 points)
        if fcf_yield > 8:
            score += 40
        elif fcf_yield > 5:
            score += 30
        elif fcf_yield > 3:
            score += 20
        elif fcf_yield > 0:
            score += 10
        
        # Dividend component (0-20 points)
        if dividend_yield > 3:
            score += 20
        elif dividend_yield > 1:
            score += 10
        
        return score
    
    def _calculate_dcf(self, stock, metrics: Dict) -> Dict:
        """Calculate DCF intrinsic value and margin of safety."""
        try:
            current_price = metrics['current_price']
            
            # Get FCF data
            cashflow = stock.cashflow
            if cashflow.empty:
                return {'intrinsic_value': current_price, 'margin_of_safety': 0}
            
            fcf = cashflow.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cashflow.index else 0
            
            if fcf <= 0:
                return {'intrinsic_value': current_price, 'margin_of_safety': 0}
            
            # Get shares outstanding for per-share calculation
            shares_outstanding = stock.info.get('sharesOutstanding', 0)
            if not shares_outstanding or shares_outstanding <= 0:
                return {'intrinsic_value': current_price, 'margin_of_safety': 0}
            
            # DCF parameters
            discount_rate = self.analyzer_config.get('discount_rate', 0.08)
            terminal_growth = self.analyzer_config.get('terminal_growth', 0.02)
            explicit_growth = self.analyzer_config.get('explicit_growth', 0.06)
            growth_years = self.analyzer_config.get('growth_years', 5)
            
            # Calculate DCF (enterprise value)
            enterprise_value = self._dcf_calculation(fcf, explicit_growth, terminal_growth, 
                                                   discount_rate, growth_years)
            
            # Convert to per-share intrinsic value
            intrinsic_value_per_share = enterprise_value / shares_outstanding
            
            # Calculate margin of safety
            margin_of_safety = ((intrinsic_value_per_share - current_price) / intrinsic_value_per_share) * 100
            
            return {
                'intrinsic_value': intrinsic_value_per_share,
                'margin_of_safety': margin_of_safety
            }
            
        except Exception as e:
            logger.error(f"Error in DCF calculation: {e}")
            return {'intrinsic_value': current_price, 'margin_of_safety': 0}
    
    def _dcf_calculation(self, fcf: float, explicit_growth: float, terminal_growth: float,
                        discount_rate: float, growth_years: int) -> float:
        """Perform DCF calculation."""
        # Explicit period
        pv_explicit = 0
        for year in range(1, growth_years + 1):
            future_fcf = fcf * ((1 + explicit_growth) ** year)
            pv_explicit += future_fcf / ((1 + discount_rate) ** year)
        
        # Terminal value
        terminal_fcf = fcf * ((1 + explicit_growth) ** growth_years) * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** growth_years)
        
        return pv_explicit + pv_terminal 