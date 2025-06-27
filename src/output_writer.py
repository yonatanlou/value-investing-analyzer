"""
Output writer module for generating CSV reports and console output.
Uses Rich for beautiful console formatting and pandas for CSV export.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)


class OutputWriter:
    """Handles output generation for CSV reports and console display."""
    
    def __init__(self, config: Dict):
        """Initialize output writer with configuration."""
        self.config = config
        self.output_config = config.get('output', {})
        self.console = Console()
        
    def write_output(self, ranked_stocks: List[Dict], summary_stats: Dict) -> None:
        """Write both CSV and console output."""
        if self.output_config.get('save_csv', True):
            self._write_csv(ranked_stocks)
        
        if self.output_config.get('console_display', True):
            self._write_console(ranked_stocks, summary_stats)
    
    def _write_csv(self, ranked_stocks: List[Dict]) -> None:
        """Write ranked stocks to CSV file."""
        if not ranked_stocks:
            logger.warning("No stocks to write to CSV")
            return
        
        # Create reports directory
        csv_path = Path(self.output_config.get('csv_path', 'reports'))
        csv_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = csv_path / f"value_radar_{timestamp}.csv"
        
        # Convert to DataFrame and save
        df = pd.DataFrame(ranked_stocks)
        
        # Reorder columns for better readability
        column_order = [
            'ticker', 'recommendation', 'composite_score', 'current_price',
            'intrinsic_value', 'margin_of_safety', 'pe_ratio', 'pb_ratio',
            'fcf_yield', 'roe', 'revenue_cagr', 'debt_to_equity', 'dividend_yield',
            'quality_score', 'health_score', 'popularity_score', 'mention_count',
            'rationale'
        ]
        
        # Only include columns that exist in the data
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        df.to_csv(filename, index=False)
        logger.info(f"CSV report saved to {filename}")
    
    def _write_console(self, ranked_stocks: List[Dict], summary_stats: Dict) -> None:
        """Write console output using Rich formatting."""
        self.console.print("\n[bold blue]Value Investing Radar Report[/bold blue]")
        self.console.print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print summary statistics
        self._print_summary(summary_stats)
        
        # Print top recommendations
        self._print_recommendations(ranked_stocks)
    
    def _print_summary(self, summary_stats: Dict) -> None:
        """Print summary statistics."""
        if not summary_stats:
            return
        
        self.console.print("\n[bold]Summary Statistics:[/bold]")
        
        # Create summary table
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Stocks Analyzed", str(summary_stats.get('total_stocks', 0)))
        table.add_row("BUY Recommendations", f"[green]{summary_stats.get('buy_count', 0)}[/green]")
        table.add_row("HOLD Recommendations", f"[yellow]{summary_stats.get('hold_count', 0)}[/yellow]")
        table.add_row("AVOID Recommendations", f"[red]{summary_stats.get('avoid_count', 0)}[/red]")
        table.add_row("Average Composite Score", f"{summary_stats.get('avg_composite_score', 0):.1f}")
        table.add_row("Average Margin of Safety", f"{summary_stats.get('avg_margin_of_safety', 0):.1f}%")
        
        self.console.print(table)
    
    def _print_recommendations(self, ranked_stocks: List[Dict]) -> None:
        """Print stock recommendations table."""
        if not ranked_stocks:
            self.console.print("\n[red]No stocks to display[/red]")
            return
        
        self.console.print("\n[bold]Top Stock Recommendations:[/bold]")
        
        # Create main table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="dim", width=4)
        table.add_column("Ticker", style="bold", width=8)
        table.add_column("Rec", style="bold", width=6)
        table.add_column("Score", style="cyan", width=8)
        table.add_column("Price", style="green", width=10)
        table.add_column("MOS%", style="yellow", width=8)
        table.add_column("P/E", width=8)
        table.add_column("ROE%", width=8)
        table.add_column("FCF%", width=8)
        table.add_column("Rationale", style="dim", width=40)
        
        # Add rows
        for i, stock in enumerate(ranked_stocks[:10], 1):  # Top 10
            # Color code recommendation
            rec = stock.get('recommendation', 'N/A')
            if rec == 'BUY':
                rec_colored = f"[green]{rec}[/green]"
            elif rec == 'HOLD':
                rec_colored = f"[yellow]{rec}[/yellow]"
            else:
                rec_colored = f"[red]{rec}[/red]"
            
            # Format values
            price = stock.get('current_price', 0)
            mos = stock.get('margin_of_safety', 0)
            pe = stock.get('pe_ratio', 0)
            roe = stock.get('roe', 0)
            fcf = stock.get('fcf_yield', 0)
            rationale = stock.get('rationale', '')[:38] + '...' if len(stock.get('rationale', '')) > 40 else stock.get('rationale', '')
            
            table.add_row(
                str(i),
                stock.get('ticker', 'N/A'),
                rec_colored,
                f"{stock.get('composite_score', 0):.1f}",
                f"${price:.2f}" if price else "N/A",
                f"{mos:.1f}%" if mos else "N/A",
                f"{pe:.1f}" if pe else "N/A",
                f"{roe:.1f}%" if roe else "N/A",
                f"{fcf:.1f}%" if fcf else "N/A",
                rationale
            )
        
        self.console.print(table)
        
        # Print additional details for top 3
        if len(ranked_stocks) >= 3:
            self.console.print("\n[bold]Detailed Analysis - Top 3:[/bold]")
            for i, stock in enumerate(ranked_stocks[:3], 1):
                self._print_stock_details(stock, i)
    
    def _print_stock_details(self, stock: Dict, rank: int) -> None:
        """Print detailed analysis for a single stock."""
        ticker = stock.get('ticker', 'N/A')
        recommendation = stock.get('recommendation', 'N/A')
        
        # Color code based on recommendation
        if recommendation == 'BUY':
            color = "green"
        elif recommendation == 'HOLD':
            color = "yellow"
        else:
            color = "red"
        
        self.console.print(f"\n[bold {color}]{rank}. {ticker} - {recommendation}[/bold {color}]")
        
        # Create details table
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="white", width=15)
        
        # Key metrics
        table.add_row("Current Price", f"${stock.get('current_price', 0):.2f}")
        table.add_row("Intrinsic Value", f"${stock.get('intrinsic_value', 0):.2f}")
        table.add_row("Margin of Safety", f"{stock.get('margin_of_safety', 0):.1f}%")
        table.add_row("Composite Score", f"{stock.get('composite_score', 0):.1f}")
        table.add_row("P/E Ratio", f"{stock.get('pe_ratio', 0):.1f}")
        table.add_row("P/B Ratio", f"{stock.get('pb_ratio', 0):.2f}")
        table.add_row("ROE", f"{stock.get('roe', 0):.1f}%")
        table.add_row("Revenue CAGR", f"{stock.get('revenue_cagr', 0):.1f}%")
        table.add_row("FCF Yield", f"{stock.get('fcf_yield', 0):.1f}%")
        table.add_row("Debt/Equity", f"{stock.get('debt_to_equity', 0):.2f}")
        table.add_row("Dividend Yield", f"{stock.get('dividend_yield', 0):.1f}%")
        table.add_row("Quality Score", f"{stock.get('quality_score', 0):.1f}")
        table.add_row("Health Score", f"{stock.get('health_score', 0):.1f}")
        table.add_row("Popularity Score", f"{stock.get('popularity_score', 0):.1f}")
        table.add_row("Mention Count", str(stock.get('mention_count', 0)))
        
        self.console.print(table)
        
        # Print rationale
        rationale = stock.get('rationale', '')
        if rationale:
            self.console.print(f"[dim]Rationale: {rationale}[/dim]") 