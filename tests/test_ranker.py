"""
Unit tests for Ranker module.
"""

import pytest
from src.ranker import Ranker


class TestRanker:
    """Test cases for Ranker."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = {
            'ranker': {
                'weights': {
                    'mos': 0.4,
                    'quality': 0.3,
                    'health': 0.2,
                    'popularity': 0.1
                },
                'thresholds': {
                    'buy': 75,
                    'hold': 50
                }
            }
        }
        self.ranker = Ranker(self.config)
    
    def test_calculate_composite_score(self):
        """Test composite score calculation."""
        stock = {
            'margin_of_safety': 25.0,  # Should get high MOS score
            'quality_score': 80.0,     # 80% quality
            'health_score': 70.0,      # 70% health
            'popularity_score': 100.0  # High popularity
        }
        
        score = self.ranker._calculate_composite_score(stock)
        
        # Score should be reasonable (0-100)
        assert 0 <= score <= 100
        assert score > 50  # Should be good with these metrics
    
    def test_assign_recommendation_buy(self):
        """Test BUY recommendation assignment."""
        recommendation = self.ranker._assign_recommendation(80.0)
        assert recommendation == 'BUY'
    
    def test_assign_recommendation_hold(self):
        """Test HOLD recommendation assignment."""
        recommendation = self.ranker._assign_recommendation(60.0)
        assert recommendation == 'HOLD'
    
    def test_assign_recommendation_avoid(self):
        """Test AVOID recommendation assignment."""
        recommendation = self.ranker._assign_recommendation(30.0)
        assert recommendation == 'AVOID'
    
    def test_normalize_mos_score(self):
        """Test margin of safety score normalization."""
        # High MOS should get high score
        assert self.ranker._normalize_mos_score(50.0) == 1.0
        assert self.ranker._normalize_mos_score(30.0) == 0.8
        
        # Negative MOS should get low score
        assert self.ranker._normalize_mos_score(-30.0) == 0.0
    
    def test_normalize_popularity_score(self):
        """Test popularity score normalization."""
        # Zero popularity should get zero score
        assert self.ranker._normalize_popularity_score(0.0) == 0.0
        
        # High popularity should get high score (but capped)
        high_score = self.ranker._normalize_popularity_score(1000.0)
        assert 0.0 < high_score <= 1.0
    
    def test_generate_rationale(self):
        """Test rationale generation."""
        stock = {
            'margin_of_safety': 25.0,
            'roe': 18.0,
            'revenue_cagr': 12.0,
            'debt_to_equity': 0.3,
            'fcf_yield': 8.0,
            'pe_ratio': 12.0
        }
        
        rationale = self.ranker._generate_rationale(stock, 85.0)
        
        # Should contain key metrics
        assert 'MOS=25.0%' in rationale
        assert 'Strong ROE=18.0%' in rationale
        assert 'High growth=12.0%' in rationale
        assert 'Low debt' in rationale
        assert 'Strong FCF=8.0%' in rationale
        assert 'Low P/E=12.0' in rationale
    
    def test_rank_stocks(self):
        """Test full stock ranking process."""
        stocks = [
            {
                'ticker': 'AAPL',
                'margin_of_safety': 30.0,
                'quality_score': 85.0,
                'health_score': 80.0,
                'popularity_score': 100.0
            },
            {
                'ticker': 'MSFT',
                'margin_of_safety': 15.0,
                'quality_score': 75.0,
                'health_score': 70.0,
                'popularity_score': 80.0
            },
            {
                'ticker': 'TSLA',
                'margin_of_safety': -10.0,
                'quality_score': 60.0,
                'health_score': 50.0,
                'popularity_score': 120.0
            }
        ]
        
        ranked = self.ranker.rank_stocks(stocks)
        
        # Should have all stocks ranked
        assert len(ranked) == 3
        
        # Should have composite scores and recommendations
        for stock in ranked:
            assert 'composite_score' in stock
            assert 'recommendation' in stock
            assert 'rationale' in stock
        
        # AAPL should rank highest (best metrics)
        assert ranked[0]['ticker'] == 'AAPL'
        assert ranked[0]['recommendation'] == 'BUY'
        
        # TSLA should rank lowest (negative MOS)
        assert ranked[2]['ticker'] == 'TSLA'
    
    def test_get_summary_stats(self):
        """Test summary statistics calculation."""
        ranked_stocks = [
            {'recommendation': 'BUY', 'composite_score': 85.0, 'margin_of_safety': 25.0},
            {'recommendation': 'BUY', 'composite_score': 80.0, 'margin_of_safety': 20.0},
            {'recommendation': 'HOLD', 'composite_score': 60.0, 'margin_of_safety': 5.0},
            {'recommendation': 'AVOID', 'composite_score': 30.0, 'margin_of_safety': -10.0}
        ]
        
        stats = self.ranker.get_summary_stats(ranked_stocks)
        
        assert stats['total_stocks'] == 4
        assert stats['buy_count'] == 2
        assert stats['hold_count'] == 1
        assert stats['avoid_count'] == 1
        assert stats['avg_composite_score'] == 63.75
        assert stats['avg_margin_of_safety'] == 10.0
    
    def test_empty_stocks(self):
        """Test handling of empty stock list."""
        ranked = self.ranker.rank_stocks([])
        assert ranked == []
        
        stats = self.ranker.get_summary_stats([])
        assert stats == {} 