"""
Output writer module for generating CSV reports, HTML reports, and console output.
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
    """Handles output generation for CSV reports, HTML reports, and console display."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.output_config = config.get('output', {})
        self.console = Console()
        
    def write_output(self, ranked_stocks: List[Dict], summary_stats: Dict) -> None:
        """Write CSV, HTML, and console output."""
        if self.output_config.get('save_csv', True):
            self._write_csv(ranked_stocks)
        if self.output_config.get('save_html', True):
            self._write_html(ranked_stocks, summary_stats)
        if self.output_config.get('console_display', True):
            self._write_console(ranked_stocks, summary_stats)
    
    def _write_csv(self, ranked_stocks: List[Dict]) -> None:
        """Write ranked stocks to CSV file."""
        if not ranked_stocks:
            return
        
        csv_path = Path(self.output_config.get('csv_path', 'reports'))
        csv_path.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(ranked_stocks)
        column_order = ['ticker', 'recommendation', 'composite_score', 'current_price', 'intrinsic_value', 
                       'margin_of_safety', 'pe_ratio', 'pb_ratio', 'fcf_yield', 'roe', 'revenue_cagr', 
                       'debt_to_equity', 'dividend_yield', 'quality_score', 'health_score', 'popularity_score', 
                       'mention_count', 'reddit_links', 'rationale']
        existing_columns = [col for col in column_order if col in df.columns]
        df[existing_columns].to_csv(csv_path / f"value_radar_{datetime.now().strftime('%Y-%m-%d')}.csv", index=False)
        logger.info(f"CSV report saved to {csv_path}")
    
    def _write_html(self, ranked_stocks: List[Dict], summary_stats: Dict) -> None:
        """Write detailed HTML report."""
        if not ranked_stocks:
            return
        
        html_path = Path(self.output_config.get('html_path', 'reports'))
        html_path.mkdir(parents=True, exist_ok=True)
        
        # Get the raw posts data for the Reddit posts section
        raw_posts = self._load_raw_posts()
        
        html_content = self._generate_html_content(ranked_stocks, summary_stats, raw_posts)
        with open(html_path / f"value_radar_{datetime.now().strftime('%Y-%m-%d')}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML report saved to {html_path}")
    
    def _load_raw_posts(self) -> List[Dict]:
        """Load raw posts data from the saved JSON file."""
        try:
            import json
            data_file = Path(f"data/raw/{datetime.now().strftime('%Y-%m-%d')}.json")
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load raw posts data: {e}")
        return []
    
    def _generate_html_content(self, ranked_stocks: List[Dict], summary_stats: Dict, raw_posts: List[Dict]) -> str:
        """Generate complete HTML content with styling and interactivity."""
        css = """
        <style>
            body{font-family:'Segoe UI',sans-serif;margin:0;padding:20px;background:#f5f5f5}
            .container{max-width:1200px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
            .header{text-align:center;margin-bottom:30px;padding-bottom:20px;border-bottom:2px solid #e0e0e0}
            .header h1{color:#2c3e50;margin:0;font-size:2.5em}
            .summary-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px}
            .stat-card{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;border-radius:8px;text-align:center}
            .stat-card h3{margin:0 0 10px 0;font-size:1.2em}
            .stat-card .value{font-size:2em;font-weight:bold}
            .stock-table{width:100%;border-collapse:collapse;margin-bottom:20px;background:white;border-radius:8px;overflow:hidden;box-shadow:0 2px 5px rgba(0,0,0,0.1)}
            .stock-table th{background:#34495e;color:white;padding:15px 10px;text-align:left;font-weight:600;cursor:pointer}
            .stock-table td{padding:12px 10px;border-bottom:1px solid #ecf0f1}
            .stock-table tr:hover{background:#f8f9fa}
            .recommendation-buy{background:#d4edda;color:#155724;padding:4px 8px;border-radius:4px;font-weight:bold}
            .recommendation-hold{background:#fff3cd;color:#856404;padding:4px 8px;border-radius:4px;font-weight:bold}
            .recommendation-avoid{background:#f8d7da;color:#721c24;padding:4px 8px;border-radius:4px;font-weight:bold}
            .score-high{color:#27ae60;font-weight:bold}
            .score-medium{color:#f39c12;font-weight:bold}
            .score-low{color:#e74c3c;font-weight:bold}
            .stock-detail{background:#f8f9fa;border-radius:8px;padding:20px;margin-bottom:20px;border-left:4px solid #3498db;display:none}
            .metrics-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin-bottom:15px}
            .metric{background:white;padding:10px;border-radius:5px;border:1px solid #e0e0e0}
            .metric-label{font-size:0.9em;color:#7f8c8d;margin-bottom:5px}
            .metric-value{font-size:1.1em;font-weight:bold;color:#2c3e50}
            .rationale{background:white;padding:15px;border-radius:5px;border-left:3px solid #3498db;margin-top:15px}
            .reddit-links{margin-top:15px}
            .reddit-links ul{margin:0;padding-left:20px}
            .reddit-links a{color:#3498db;text-decoration:none}
            .reddit-links a:hover{text-decoration:underline}
            .reddit-posts{background:#f8f9fa;border-radius:8px;padding:20px;margin-bottom:20px}
            .reddit-post{background:white;border-radius:5px;padding:15px;margin-bottom:15px;border-left:3px solid #3498db}
            .post-title{font-weight:bold;color:#2c3e50;margin-bottom:10px}
            .post-content{color:#555;margin-bottom:10px;line-height:1.5}
            .post-meta{font-size:0.9em;color:#7f8c8d;margin-bottom:10px}
            .post-tickers{background:#e8f4fd;padding:10px;border-radius:4px;border-left:3px solid #3498db}
            .ticker-tag{display:inline-block;background:#3498db;color:white;padding:2px 8px;border-radius:3px;margin:2px;font-size:0.9em;font-weight:bold}
            .section-nav{background:#34495e;color:white;padding:15px;border-radius:8px;margin-bottom:20px}
            .section-nav a{color:white;text-decoration:none;margin-right:20px;padding:5px 10px;border-radius:3px}
            .section-nav a:hover{background:#2c3e50}
            .section-nav a.active{background:#3498db}
        </style>
        """
        
        js = """
        <script>
            function toggleDetails(ticker){const d=document.getElementById('detail-'+ticker);d.style.display=d.style.display==='none'||d.style.display===''?'block':'none'}
            function sortTable(c){const t=document.getElementById('stockTable'),b=t.getElementsByTagName('tbody')[0],r=Array.from(b.getElementsByTagName('tr'));
            r.sort((a,b)=>{const av=a.cells[c].textContent,bv=b.cells[c].textContent,an=parseFloat(av.replace(/[^0-9.-]/g,'')),bn=parseFloat(bv.replace(/[^0-9.-]/g,''));return !isNaN(an)&&!isNaN(bn)?bn-an:av.localeCompare(bv)});
            r.forEach(row=>b.appendChild(row))}
            function showSection(sectionId){
                // Hide all content sections
                document.querySelectorAll('.content-section').forEach(function(section) {
                    section.style.display = 'none';
                });
                // Show the selected section
                document.getElementById(sectionId).style.display = 'block';
                // Remove active class from all nav links
                document.querySelectorAll('.section-nav a').forEach(function(link) {
                    link.classList.remove('active');
                });
                // Add active class to clicked link
                event.target.classList.add('active');
            }
        </script>
        """
        
        summary_html = self._generate_summary_html(summary_stats)
        table_html = self._generate_table_html(ranked_stocks)
        details_html = self._generate_details_html(ranked_stocks)
        reddit_posts_html = self._generate_reddit_posts_html(raw_posts, ranked_stocks)
        
        return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Value Investing Radar Report - {datetime.now().strftime('%Y-%m-%d')}</title>{css}</head><body><div class="container"><div class="header"><h1>Value Investing Radar Report</h1><p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div>{summary_html}<div class="section-nav"><a href="#" onclick="showSection('recommendations')" class="active">Stock Recommendations</a><a href="#" onclick="showSection('details')">Detailed Analysis</a><a href="#" onclick="showSection('reddit-posts')">Reddit Posts</a></div><div id="recommendations" class="content-section"><h2>Stock Recommendations</h2>{table_html}</div><div id="details" class="content-section" style="display:none"><h2>Detailed Analysis</h2>{details_html}</div><div id="reddit-posts" class="content-section" style="display:none"><h2>Reddit Posts Analysis</h2>{reddit_posts_html}</div><div class="footer"><p>Generated by Value Investing Radar | Data from Reddit r/valueinvesting</p></div></div>{js}</body></html>"""
    
    def _generate_summary_html(self, summary_stats: Dict) -> str:
        """Generate summary statistics HTML."""
        if not summary_stats:
            return ""
        stats = summary_stats
        return f"""<div class="summary-stats"><div class="stat-card"><h3>Total Stocks</h3><div class="value">{stats.get('total_stocks',0)}</div></div><div class="stat-card"><h3>BUY Recommendations</h3><div class="value">{stats.get('buy_count',0)}</div></div><div class="stat-card"><h3>HOLD Recommendations</h3><div class="value">{stats.get('hold_count',0)}</div></div><div class="stat-card"><h3>AVOID Recommendations</h3><div class="value">{stats.get('avoid_count',0)}</div></div><div class="stat-card"><h3>Avg Composite Score</h3><div class="value">{stats.get('avg_composite_score',0):.1f}</div></div><div class="stat-card"><h3>Avg Margin of Safety</h3><div class="value">{stats.get('avg_margin_of_safety',0):.1f}%</div></div></div>"""
    
    def _generate_table_html(self, ranked_stocks: List[Dict]) -> str:
        """Generate main recommendations table HTML."""
        if not ranked_stocks:
            return "<p>No stocks to display</p>"
        
        headers = ['Rank','Ticker','Recommendation','Score','Price','MOS%','P/E','ROE%','FCF%','Links','Actions']
        table_html = f"""<table class="stock-table" id="stockTable"><thead><tr>{''.join(f'<th onclick="sortTable({i})" style="cursor:pointer;">{h}</th>' for i,h in enumerate(headers))}</tr></thead><tbody>"""
        
        for i, stock in enumerate(ranked_stocks, 1):
            ticker = stock.get('ticker', 'N/A')
            rec = stock.get('recommendation', 'N/A')
            rec_class = f"recommendation-{rec.lower()}"
            score = stock.get('composite_score', 0)
            score_class = "score-high" if score >= 75 else "score-medium" if score >= 50 else "score-low"
            
            table_html += f"""<tr><td>{i}</td><td><strong>{ticker}</strong></td><td><span class="{rec_class}">{rec}</span></td><td class="{score_class}">{score:.1f}</td><td>${stock.get('current_price',0):.2f}</td><td>{stock.get('margin_of_safety',0):.1f}%</td><td>{stock.get('pe_ratio',0):.1f}</td><td>{stock.get('roe',0):.1f}%</td><td>{stock.get('fcf_yield',0):.1f}%</td><td>{len(stock.get('reddit_links',[]))}</td><td><button onclick="toggleDetails('{ticker}')" style="padding:5px 10px;background:#3498db;color:white;border:none;border-radius:3px;cursor:pointer;">Details</button></td></tr>"""
        
        return table_html + "</tbody></table>"
    
    def _generate_details_html(self, ranked_stocks: List[Dict]) -> str:
        """Generate detailed analysis HTML for each stock."""
        if not ranked_stocks:
            return ""
        
        details_html = ""
        metrics = ['current_price','intrinsic_value','margin_of_safety','composite_score','pe_ratio','pb_ratio','roe','revenue_cagr','fcf_yield','debt_to_equity','dividend_yield','quality_score','health_score','popularity_score','mention_count']
        metric_labels = ['Current Price','Intrinsic Value','Margin of Safety','Composite Score','P/E Ratio','P/B Ratio','ROE','Revenue CAGR','FCF Yield','Debt/Equity','Dividend Yield','Quality Score','Health Score','Popularity Score','Mention Count']
        
        for stock in ranked_stocks:
            ticker = stock.get('ticker', 'N/A')
            rec = stock.get('recommendation', 'N/A')
            rec_class = f"recommendation-{rec.lower()}"
            
            metrics_html = ""
            for metric, label in zip(metrics, metric_labels):
                value = stock.get(metric, 0)
                if 'price' in metric or 'value' in metric:
                    formatted_value = f"{value:.2f}"
                elif metric == 'mention_count':
                    formatted_value = str(int(value))
                else:
                    formatted_value = f"{value:.1f}"
                
                suffix = '%' if any(x in metric for x in ['yield', 'roe', 'cagr', 'safety']) else ''
                metrics_html += f"""<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{formatted_value}{suffix}</div></div>"""
            
            links_html = ""
            reddit_links = stock.get('reddit_links', [])
            if reddit_links:
                links_html = f"""<div class="reddit-links"><h4>Reddit Discussion Links ({len(reddit_links)})</h4><ul>{''.join(f'<li><a href="{link}" target="_blank">{link}</a></li>' for link in reddit_links)}</ul></div>"""
            
            details_html += f"""<div class="stock-detail" id="detail-{ticker}"><h3>{ticker} - <span class="{rec_class}">{rec}</span></h3><div class="metrics-grid">{metrics_html}</div>{links_html}<div class="rationale"><strong>Analysis Rationale:</strong><br>{stock.get('rationale','')}</div></div>"""
        
        return details_html
    
    def _generate_reddit_posts_html(self, raw_posts: List[Dict], ranked_stocks: List[Dict]) -> str:
        """Generate Reddit posts section with ticker mentions."""
        if not raw_posts:
            return "<p>No Reddit posts data available</p>"
        
        # Create a mapping of tickers to their data for quick lookup
        ticker_data = {stock['ticker']: stock for stock in ranked_stocks}
        
        # Create a mapping of posts to their mentioned tickers
        post_tickers = {}
        for stock in ranked_stocks:
            ticker = stock['ticker']
            reddit_links = stock.get('reddit_links', [])
            for link in reddit_links:
                if link not in post_tickers:
                    post_tickers[link] = []
                post_tickers[link].append(ticker)
        
        # Sort posts by number of mentioned tickers (descending)
        sorted_posts = sorted(raw_posts, key=lambda post: len(post_tickers.get(post.get('permalink', ''), [])), reverse=True)
        
        posts_html = ""
        for post in sorted_posts:
            permalink = post.get('permalink', '')
            title = post.get('title', 'No Title')
            selftext = post.get('selftext', '')
            score = post.get('score', 0)
            num_comments = post.get('num_comments', 0)
            created_utc = post.get('created_utc', 0)
            
            # Get mentioned tickers for this post
            mentioned_tickers = post_tickers.get(permalink, [])
            
            # Format creation date
            try:
                from datetime import datetime
                created_date = datetime.fromtimestamp(created_utc).strftime('%Y-%m-%d %H:%M')
            except:
                created_date = "Unknown"
            
            # Create ticker tags with recommendation colors
            ticker_tags = ""
            for ticker in mentioned_tickers:
                if ticker in ticker_data:
                    rec = ticker_data[ticker].get('recommendation', 'N/A')
                    rec_color = '#27ae60' if rec == 'BUY' else '#f39c12' if rec == 'HOLD' else '#e74c3c'
                    ticker_tags += f'<span class="ticker-tag" style="background:{rec_color}">{ticker} ({rec})</span>'
                else:
                    ticker_tags += f'<span class="ticker-tag">{ticker}</span>'
            
            # Truncate content if too long
            content_preview = selftext[:300] + "..." if len(selftext) > 300 else selftext
            
            posts_html += f"""
            <div class="reddit-post">
                <div class="post-title"><a href="{permalink}" target="_blank">{title}</a></div>
                <div class="post-meta">Score: {score} | Comments: {num_comments} | Posted: {created_date} | Tickers: {len(mentioned_tickers)}</div>
                <div class="post-content">{content_preview}</div>
                <div class="post-tickers">
                    <strong>Mentioned Tickers:</strong> {ticker_tags if ticker_tags else 'None detected'}
                </div>
            </div>
            """
        
        return f'<div class="reddit-posts">{posts_html}</div>'
    
    def _write_console(self, ranked_stocks: List[Dict], summary_stats: Dict) -> None:
        """Write console output using Rich formatting."""
        self.console.print("\n[bold blue]Value Investing Radar Report[/bold blue]")
        self.console.print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if summary_stats:
            table = Table(show_header=False, box=None)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            for metric, value in [("Total Stocks Analyzed", str(summary_stats.get('total_stocks', 0))), ("BUY Recommendations", f"[green]{summary_stats.get('buy_count', 0)}[/green]"), ("HOLD Recommendations", f"[yellow]{summary_stats.get('hold_count', 0)}[/yellow]"), ("AVOID Recommendations", f"[red]{summary_stats.get('avoid_count', 0)}[/red]"), ("Average Composite Score", f"{summary_stats.get('avg_composite_score', 0):.1f}"), ("Average Margin of Safety", f"{summary_stats.get('avg_margin_of_safety', 0):.1f}%")]:
                table.add_row(metric, value)
            self.console.print(table)
        
        if ranked_stocks:
            table = Table(show_header=True, header_style="bold magenta")
            for col in ["Rank", "Ticker", "Rec", "Score", "Price", "MOS%", "P/E", "ROE%", "FCF%", "Links", "Rationale"]:
                table.add_column(col, width=8 if col in ["Rank", "Rec", "Score", "P/E", "ROE%", "FCF%", "Links"] else 10 if col == "Ticker" else 30)
            
            for i, stock in enumerate(ranked_stocks[:10], 1):
                rec = stock.get('recommendation', 'N/A')
                rec_colored = f"[green]{rec}[/green]" if rec == 'BUY' else f"[yellow]{rec}[/yellow]" if rec == 'HOLD' else f"[red]{rec}[/red]"
                table.add_row(str(i), stock.get('ticker', 'N/A'), rec_colored, f"{stock.get('composite_score', 0):.1f}", f"${stock.get('current_price', 0):.2f}", f"{stock.get('margin_of_safety', 0):.1f}%", f"{stock.get('pe_ratio', 0):.1f}", f"{stock.get('roe', 0):.1f}%", f"{stock.get('fcf_yield', 0):.1f}%", str(len(stock.get('reddit_links', []))), stock.get('rationale', '')[:28] + '...' if len(stock.get('rationale', '')) > 30 else stock.get('rationale', ''))
            self.console.print(table) 