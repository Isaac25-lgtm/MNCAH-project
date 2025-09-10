"""
ReportGenerator class for generating analysis reports from MNCAH data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Union
import json
from pathlib import Path
from datetime import datetime
import logging

from .mncah_data import MNCAHData


class ReportGenerator:
    """
    Class to generate comprehensive reports and visualizations from MNCAH analysis results.
    
    Supports multiple output formats including HTML, JSON, and visualizations.
    """
    
    def __init__(self, output_dir: str = 'reports'):
        """
        Initialize ReportGenerator.
        
        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Set up matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")
    
    def generate_summary_report(self, data: MNCAHData, analysis_results: Dict, 
                              format_type: str = 'html') -> str:
        """
        Generate a comprehensive summary report.
        
        Args:
            data: MNCAHData object
            analysis_results: Results from MNCAHAnalyzer
            format_type: Output format ('html', 'json', 'text')
            
        Returns:
            Path to generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'html':
            return self._generate_html_report(data, analysis_results, timestamp)
        elif format_type == 'json':
            return self._generate_json_report(data, analysis_results, timestamp)
        elif format_type == 'text':
            return self._generate_text_report(data, analysis_results, timestamp)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _generate_html_report(self, data: MNCAHData, analysis_results: Dict, timestamp: str) -> str:
        """Generate HTML report."""
        filename = self.output_dir / f"mncah_report_{timestamp}.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MNCAH Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #2E8B57; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #2E8B57; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #2E8B57; color: white; }}
                .indicator {{ background-color: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>MNCAH Data Analysis Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Data Overview</h2>
                <div class="metric">
                    <strong>Total Records:</strong> {len(data)}
                </div>
                <div class="metric">
                    <strong>Countries:</strong> {len(data.get_countries())}
                </div>
                <div class="metric">
                    <strong>Year Range:</strong> {min(data.get_years()) if data.get_years() else 'N/A'} - {max(data.get_years()) if data.get_years() else 'N/A'}
                </div>
                <div class="metric">
                    <strong>Indicators:</strong> {len([col for col in data.data.columns if col in data.ALL_INDICATORS])}
                </div>
            </div>
        """
        
        # Add countries list
        countries = data.get_countries()
        if countries:
            html_content += f"""
            <div class="section">
                <h2>Countries Included</h2>
                <p>{', '.join(countries[:10])}{' and ' + str(len(countries)-10) + ' more...' if len(countries) > 10 else ''}</p>
            </div>
            """
        
        # Add available indicators
        indicators = [col for col in data.data.columns if col in data.ALL_INDICATORS]
        if indicators:
            html_content += """
            <div class="section">
                <h2>Available Indicators</h2>
            """
            for indicator in indicators:
                html_content += f'<div class="indicator">{indicator.replace("_", " ").title()}</div>'
            html_content += "</div>"
        
        # Add analysis results
        if 'trends' in analysis_results:
            html_content += self._format_trends_html(analysis_results['trends'])
        
        if 'country_comparison' in analysis_results:
            html_content += self._format_comparison_html(analysis_results['country_comparison'])
        
        if 'target_assessment' in analysis_results:
            html_content += self._format_targets_html(analysis_results['target_assessment'])
        
        # Add summary statistics
        stats = data.get_summary_stats()
        if stats:
            html_content += """
            <div class="section">
                <h2>Summary Statistics</h2>
                <table>
                    <tr><th>Indicator</th><th>Count</th><th>Mean</th><th>Std Dev</th><th>Min</th><th>Max</th></tr>
            """
            for indicator, stat in stats.items():
                html_content += f"""
                <tr>
                    <td>{indicator.replace('_', ' ').title()}</td>
                    <td>{stat['count']}</td>
                    <td>{stat['mean']:.2f}</td>
                    <td>{stat['std']:.2f}</td>
                    <td>{stat['min']:.2f}</td>
                    <td>{stat['max']:.2f}</td>
                </tr>
                """
            html_content += "</table></div>"
        
        html_content += """
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report generated: {filename}")
        return str(filename)
    
    def _format_trends_html(self, trends: Dict) -> str:
        """Format trends analysis for HTML report."""
        html = """
        <div class="section">
            <h2>Trend Analysis</h2>
        """
        
        for indicator, trend_data in trends.items():
            direction = trend_data.get('overall_trend', 'unknown')
            color = 'green' if direction == 'improving' else 'red' if direction == 'worsening' else 'orange'
            
            html += f"""
            <div class="indicator">
                <h3>{indicator.replace('_', ' ').title()}</h3>
                <p><strong>Overall Trend:</strong> <span style="color: {color};">{direction.title()}</span></p>
                <p><strong>Data Points:</strong> {trend_data.get('data_points', 0)}</p>
                <p><strong>Year Range:</strong> {trend_data.get('year_range', ['N/A', 'N/A'])[0]} - {trend_data.get('year_range', ['N/A', 'N/A'])[1]}</p>
                <p><strong>Latest Value:</strong> {trend_data.get('latest_value', 'N/A') if not isinstance(trend_data.get('latest_value'), (int, float)) else f"{trend_data.get('latest_value'):.2f}"}</p>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _format_comparison_html(self, comparisons: Dict) -> str:
        """Format country comparison for HTML report."""
        html = """
        <div class="section">
            <h2>Country Comparison</h2>
        """
        
        for indicator, comp_data in comparisons.items():
            html += f"""
            <div class="indicator">
                <h3>{indicator.replace('_', ' ').title()}</h3>
                <p><strong>Year:</strong> {comp_data.get('year', 'N/A')}</p>
                <p><strong>Countries Analyzed:</strong> {comp_data.get('countries_count', 0)}</p>
                <p><strong>Best Performing:</strong> {comp_data.get('best_performing', {}).get('country', 'N/A')} 
                   ({comp_data.get('best_performing', {}).get('value', 'N/A') if not isinstance(comp_data.get('best_performing', {}).get('value'), (int, float)) else f"{comp_data.get('best_performing', {}).get('value'):.2f}"})</p>
                <p><strong>Worst Performing:</strong> {comp_data.get('worst_performing', {}).get('country', 'N/A')} 
                   ({comp_data.get('worst_performing', {}).get('value', 'N/A') if not isinstance(comp_data.get('worst_performing', {}).get('value'), (int, float)) else f"{comp_data.get('worst_performing', {}).get('value'):.2f}"})</p>
                <p><strong>Average:</strong> {comp_data.get('average', 'N/A') if not isinstance(comp_data.get('average'), (int, float)) else f"{comp_data.get('average'):.2f}"}</p>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _format_targets_html(self, targets: Dict) -> str:
        """Format target assessment for HTML report."""
        html = """
        <div class="section">
            <h2>Target Assessment</h2>
        """
        
        for indicator, target_data in targets.items():
            percentage = target_data.get('percentage_meeting_target', 0)
            color = 'green' if percentage > 70 else 'orange' if percentage > 40 else 'red'
            
            html += f"""
            <div class="indicator">
                <h3>{indicator.replace('_', ' ').title()}</h3>
                <p><strong>Target Value:</strong> {target_data.get('target_value', 'N/A')}</p>
                <p><strong>Countries Meeting Target:</strong> <span style="color: {color};">{target_data.get('countries_meeting_target', 0)} / {target_data.get('countries_assessed', 0)} ({percentage:.1f}%)</span></p>
                <p><strong>Average Value:</strong> {target_data.get('average_value', 'N/A') if not isinstance(target_data.get('average_value'), (int, float)) else f"{target_data.get('average_value'):.2f}"}</p>
                <p><strong>Gap to Target:</strong> {target_data.get('gap_to_target', 'N/A') if not isinstance(target_data.get('gap_to_target'), (int, float)) else f"{target_data.get('gap_to_target'):.2f}"}</p>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _generate_json_report(self, data: MNCAHData, analysis_results: Dict, timestamp: str) -> str:
        """Generate JSON report."""
        filename = self.output_dir / f"mncah_report_{timestamp}.json"
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            else:
                return obj
        
        report_data = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_overview': {
                    'total_records': len(data),
                    'countries': data.get_countries(),
                    'years': data.get_years(),
                    'indicators': [col for col in data.data.columns if col in data.ALL_INDICATORS]
                }
            },
            'summary_statistics': convert_types(data.get_summary_stats()),
            'analysis_results': convert_types(analysis_results)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"JSON report generated: {filename}")
        return str(filename)
    
    def _generate_text_report(self, data: MNCAHData, analysis_results: Dict, timestamp: str) -> str:
        """Generate plain text report."""
        filename = self.output_dir / f"mncah_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("MNCAH DATA ANALYSIS REPORT\\n")
            f.write("=" * 50 + "\\n\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            # Data overview
            f.write("DATA OVERVIEW\\n")
            f.write("-" * 20 + "\\n")
            f.write(f"Total Records: {len(data)}\\n")
            f.write(f"Countries: {len(data.get_countries())}\\n")
            f.write(f"Years: {min(data.get_years()) if data.get_years() else 'N/A'} - {max(data.get_years()) if data.get_years() else 'N/A'}\\n")
            f.write(f"Indicators: {len([col for col in data.data.columns if col in data.ALL_INDICATORS])}\\n\\n")
            
            # Countries
            countries = data.get_countries()
            if countries:
                f.write("COUNTRIES\\n")
                f.write("-" * 20 + "\\n")
                f.write(", ".join(countries) + "\\n\\n")
            
            # Summary statistics
            stats = data.get_summary_stats()
            if stats:
                f.write("SUMMARY STATISTICS\\n")
                f.write("-" * 20 + "\\n")
                for indicator, stat in stats.items():
                    f.write(f"{indicator.replace('_', ' ').title()}:\\n")
                    f.write(f"  Count: {stat['count']}\\n")
                    f.write(f"  Mean: {stat['mean']:.2f}\\n")
                    f.write(f"  Std: {stat['std']:.2f}\\n")
                    f.write(f"  Range: {stat['min']:.2f} - {stat['max']:.2f}\\n\\n")
        
        self.logger.info(f"Text report generated: {filename}")
        return str(filename)
    
    def create_visualization(self, data: MNCAHData, indicator: str, 
                           chart_type: str = 'trend', countries: Optional[List[str]] = None) -> str:
        """
        Create visualization for specific indicator.
        
        Args:
            data: MNCAHData object
            indicator: Indicator to visualize
            chart_type: Type of chart ('trend', 'bar', 'box')
            countries: List of countries to include (default: all)
            
        Returns:
            Path to saved visualization
        """
        if indicator not in data.data.columns:
            raise ValueError(f"Indicator {indicator} not found in data")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{indicator}_{chart_type}_{timestamp}.png"
        
        # Filter data
        plot_data = data.data.copy()
        if countries:
            plot_data = plot_data[plot_data['country'].isin(countries)]
        
        # Remove missing values
        plot_data = plot_data.dropna(subset=[indicator])
        
        if plot_data.empty:
            self.logger.warning(f"No data available for visualization of {indicator}")
            return ""
        
        plt.figure(figsize=(12, 8))
        
        if chart_type == 'trend':
            self._create_trend_plot(plot_data, indicator)
        elif chart_type == 'bar':
            self._create_bar_plot(plot_data, indicator)
        elif chart_type == 'box':
            self._create_box_plot(plot_data, indicator)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        plt.title(f"{indicator.replace('_', ' ').title()} - {chart_type.title()} Chart")
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Visualization saved: {filename}")
        return str(filename)
    
    def _create_trend_plot(self, data: pd.DataFrame, indicator: str):
        """Create trend line plot."""
        for country in data['country'].unique():
            country_data = data[data['country'] == country]
            if len(country_data) > 1:
                plt.plot(country_data['year'], country_data[indicator], 
                        marker='o', label=country, linewidth=2)
        
        plt.xlabel('Year')
        plt.ylabel(indicator.replace('_', ' ').title())
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
    
    def _create_bar_plot(self, data: pd.DataFrame, indicator: str):
        """Create bar plot for latest year."""
        latest_year = data['year'].max()
        latest_data = data[data['year'] == latest_year]
        
        plt.bar(latest_data['country'], latest_data[indicator])
        plt.xlabel('Country')
        plt.ylabel(indicator.replace('_', ' ').title())
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
    
    def _create_box_plot(self, data: pd.DataFrame, indicator: str):
        """Create box plot by country."""
        countries = data['country'].unique()
        values_by_country = [data[data['country'] == country][indicator].values 
                            for country in countries]
        
        plt.boxplot(values_by_country, labels=countries)
        plt.xlabel('Country')
        plt.ylabel(indicator.replace('_', ' ').title())
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
    
    def create_dashboard_summary(self, data: MNCAHData, analysis_results: Dict) -> str:
        """
        Create a dashboard-style summary visualization.
        
        Args:
            data: MNCAHData object
            analysis_results: Results from analysis
            
        Returns:
            Path to saved dashboard image
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"mncah_dashboard_{timestamp}.png"
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('MNCAH Data Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # Plot 1: Data coverage over time
        ax1 = axes[0, 0]
        if 'year' in data.data.columns:
            year_counts = data.data['year'].value_counts().sort_index()
            ax1.bar(year_counts.index, year_counts.values)
            ax1.set_title('Data Coverage by Year')
            ax1.set_xlabel('Year')
            ax1.set_ylabel('Number of Records')
        
        # Plot 2: Country coverage
        ax2 = axes[0, 1]
        if 'country' in data.data.columns:
            country_counts = data.data['country'].value_counts().head(10)
            ax2.barh(range(len(country_counts)), country_counts.values)
            ax2.set_yticks(range(len(country_counts)))
            ax2.set_yticklabels(country_counts.index)
            ax2.set_title('Top 10 Countries by Records')
            ax2.set_xlabel('Number of Records')
        
        # Plot 3: Indicator availability
        ax3 = axes[1, 0]
        indicators = [col for col in data.data.columns if col in data.ALL_INDICATORS]
        if indicators:
            indicator_completeness = []
            for ind in indicators[:10]:  # Top 10 indicators
                completeness = (data.data[ind].notna().sum() / len(data.data)) * 100
                indicator_completeness.append(completeness)
            
            ax3.barh(range(len(indicators[:10])), indicator_completeness)
            ax3.set_yticks(range(len(indicators[:10])))
            ax3.set_yticklabels([ind.replace('_', ' ').title() for ind in indicators[:10]])
            ax3.set_title('Data Completeness by Indicator (%)')
            ax3.set_xlabel('Completeness (%)')
        
        # Plot 4: Summary metrics
        ax4 = axes[1, 1]
        metrics = [
            f"Countries: {len(data.get_countries())}",
            f"Years: {len(data.get_years())}",
            f"Records: {len(data)}",
            f"Indicators: {len(indicators)}"
        ]
        
        ax4.text(0.1, 0.8, "\\n".join(metrics), fontsize=14, transform=ax4.transAxes,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        ax4.set_title('Data Summary')
        ax4.axis('off')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Dashboard saved: {filename}")
        return str(filename)