"""
Ranker module for scoring and categorizing stocks into Buy/Hold/Avoid recommendations.
Implements weighted scoring based on value investing principles.
"""

import logging
import math
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class Ranker:
    """Ranks stocks based on value investing criteria and assigns recommendations."""
    
    def __init__(self, config: Dict):
        """Initialize ranker with configuration."""
        self.config = config
        self.ranker_config = config.get('ranker', {})
        
    def rank_stocks(self, analyzed_stocks: List[Dict]) -> List[Dict]:
        """Rank stocks and assign Buy/Hold/Avoid recommendations."""
        if not analyzed_stocks:
            return []
        
        # Calculate composite scores
        scored_stocks = []
        for stock in analyzed_stocks:
            score = self._calculate_composite_score(stock)
            recommendation = self._assign_recommendation(score)
            rationale = self._generate_rationale(stock, score)
            
            scored_stock = {
                **stock,
                'composite_score': score,
                'recommendation': recommendation,
                'rationale': rationale
            }
            scored_stocks.append(scored_stock)
        
        # Sort by composite score descending
        scored_stocks.sort(key=lambda x: x['composite_score'], reverse=True)
        
        logger.info(f"Ranked {len(scored_stocks)} stocks")
        return scored_stocks
    
    def _calculate_composite_score(self, stock: Dict) -> float:
        """Calculate weighted composite score based on value investing criteria."""
        weights = self.ranker_config.get('weights', {})
        
        # Extract component scores
        mos_score = self._normalize_mos_score(stock.get('margin_of_safety', 0))
        quality_score = stock.get('quality_score', 0) / 100  # Normalize to 0-1
        health_score = stock.get('health_score', 0) / 100   # Normalize to 0-1
        popularity_score = self._normalize_popularity_score(stock.get('popularity_score', 0))
        
        # Calculate weighted score
        composite_score = (
            weights.get('mos', 0.4) * mos_score +
            weights.get('quality', 0.3) * quality_score +
            weights.get('health', 0.2) * health_score +
            weights.get('popularity', 0.1) * popularity_score
        )
        
        return composite_score * 100  # Convert to 0-100 scale
    
    def _normalize_mos_score(self, margin_of_safety: float) -> float:
        """Normalize margin of safety to 0-1 scale."""
        # MOS can be negative (overvalued) or positive (undervalued)
        # We want to reward positive MOS and penalize negative MOS
        if margin_of_safety >= 50:
            return 1.0
        elif margin_of_safety >= 30:
            return 0.8
        elif margin_of_safety >= 20:
            return 0.6
        elif margin_of_safety >= 10:
            return 0.4
        elif margin_of_safety >= 0:
            return 0.2
        elif margin_of_safety >= -20:
            return 0.1
        else:
            return 0.0
    
    def _normalize_popularity_score(self, popularity_score: float) -> float:
        """Normalize popularity score to 0-1 scale."""
        # Popularity scores can vary widely, so we use a log-based normalization
        if popularity_score <= 0:
            return 0.0
        
        # Use log scale to compress high values
        normalized = min(1.0, math.log10(popularity_score + 1) / 3.0)
        return normalized
    
    def _assign_recommendation(self, composite_score: float) -> str:
        """Assign Buy/Hold/Avoid recommendation based on composite score."""
        thresholds = self.ranker_config.get('thresholds', {})
        buy_threshold = thresholds.get('buy', 75)
        hold_threshold = thresholds.get('hold', 50)
        
        if composite_score >= buy_threshold:
            return 'BUY'
        elif composite_score >= hold_threshold:
            return 'HOLD'
        else:
            return 'AVOID'
    
    def _generate_rationale(self, stock: Dict, composite_score: float) -> str:
        """Generate human-readable rationale for the recommendation."""
        parts = []
        
        # Margin of Safety
        mos = stock.get('margin_of_safety', 0)
        if mos > 20:
            parts.append(f"MOS={mos:.1f}%")
        elif mos > 0:
            parts.append(f"MOS={mos:.1f}%")
        else:
            parts.append(f"Overvalued (MOS={mos:.1f}%)")
        
        # Quality indicators
        roe = stock.get('roe', 0)
        if roe > 15:
            parts.append(f"Strong ROE={roe:.1f}%")
        elif roe > 10:
            parts.append(f"Good ROE={roe:.1f}%")
        
        revenue_cagr = stock.get('revenue_cagr', 0)
        if revenue_cagr > 10:
            parts.append(f"High growth={revenue_cagr:.1f}%")
        elif revenue_cagr > 5:
            parts.append(f"Moderate growth={revenue_cagr:.1f}%")
        
        # Financial health
        debt_to_equity = stock.get('debt_to_equity', 0)
        if debt_to_equity < 0.5:
            parts.append("Low debt")
        elif debt_to_equity > 1.0:
            parts.append("High debt")
        
        fcf_yield = stock.get('fcf_yield', 0)
        if fcf_yield > 5:
            parts.append(f"Strong FCF={fcf_yield:.1f}%")
        
        # Valuation
        pe_ratio = stock.get('pe_ratio', 0)
        if pe_ratio > 0 and pe_ratio < 15:
            parts.append(f"Low P/E={pe_ratio:.1f}")
        elif pe_ratio > 25:
            parts.append(f"High P/E={pe_ratio:.1f}")
        
        # Combine parts
        if parts:
            return ", ".join(parts)
        else:
            return f"Score: {composite_score:.1f}"
    
    def get_summary_stats(self, ranked_stocks: List[Dict]) -> Dict:
        """Get summary statistics of the ranked stocks."""
        if not ranked_stocks:
            return {}
        
        buy_count = sum(1 for stock in ranked_stocks if stock['recommendation'] == 'BUY')
        hold_count = sum(1 for stock in ranked_stocks if stock['recommendation'] == 'HOLD')
        avoid_count = sum(1 for stock in ranked_stocks if stock['recommendation'] == 'AVOID')
        
        avg_score = sum(stock['composite_score'] for stock in ranked_stocks) / len(ranked_stocks)
        avg_mos = sum(stock.get('margin_of_safety', 0) for stock in ranked_stocks) / len(ranked_stocks)
        
        return {
            'total_stocks': len(ranked_stocks),
            'buy_count': buy_count,
            'hold_count': hold_count,
            'avoid_count': avoid_count,
            'avg_composite_score': avg_score,
            'avg_margin_of_safety': avg_mos
        } 