#!/usr/bin/env python3
"""
CSV Data Conversion Utility for Research Papers

This script converts research CSV data to various formats including:
- Formatted markdown tables
- PNG table images
- Statistical summaries
- Custom visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
from typing import Dict, List, Optional

class CSVAnalyzer:
    """Analyze and convert CSV research data to multiple formats."""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.clean_data()
    
    def clean_data(self):
        """Clean and prepare data for analysis."""
        # Round numerical columns for better display
        if 'position_gb' in self.df.columns:
            self.df['position_gb'] = self.df['position_gb'].round(2)
        if 'gztool_time' in self.df.columns:
            self.df['gztool_time'] = self.df['gztool_time'].round(4)
        if 'estimated_linear_time' in self.df.columns:
            self.df['estimated_linear_time'] = self.df['estimated_linear_time'].round(2)
        if 'speedup' in self.df.columns:
            self.df['speedup'] = self.df['speedup'].round(1)
    
    def generate_summary_stats(self) -> Dict:
        """Generate comprehensive summary statistics."""
        stats = {}
        
        if 'speedup' in self.df.columns:
            speedup_stats = self.df['speedup'].describe()
            stats['speedup'] = {
                'count': int(speedup_stats['count']),
                'mean': speedup_stats['mean'],
                'std': speedup_stats['std'],
                'min': speedup_stats['min'],
                'q25': speedup_stats['25%'],
                'median': speedup_stats['50%'],
                'q75': speedup_stats['75%'],
                'max': speedup_stats['max']
            }
        
        if 'gztool_time' in self.df.columns:
            time_stats = self.df['gztool_time'].describe()
            stats['access_time'] = {
                'mean_ms': time_stats['mean'] * 1000,
                'std_ms': time_stats['std'] * 1000,
                'min_ms': time_stats['min'] * 1000,
                'max_ms': time_stats['max'] * 1000
            }
        
        if 'success' in self.df.columns:
            stats['success_rate'] = self.df['success'].mean() * 100
        
        return stats
    
    def create_markdown_table(self, columns: Optional[List[str]] = None, 
                            max_rows: Optional[int] = None) -> str:
        """Create a markdown table from the data."""
        
        if columns is None:
            # Select key columns for display
            columns = [
                'test_id', 'index_point', 'position_gb', 'gztool_time', 
                'estimated_linear_time', 'speedup', 'success'
            ]
        
        # Filter to existing columns
        available_columns = [col for col in columns if col in self.df.columns]
        display_df = self.df[available_columns].copy()
        
        if max_rows:
            display_df = display_df.head(max_rows)
        
        # Create markdown table
        markdown_lines = []
        
        # Header
        headers = [col.replace('_', ' ').title() for col in available_columns]
        markdown_lines.append("| " + " | ".join(headers) + " |")
        
        # Separator
        separators = ["---"] * len(headers)
        markdown_lines.append("| " + " | ".join(separators) + " |")
        
        # Data rows
        for _, row in display_df.iterrows():
            formatted_row = []
            for col in available_columns:
                value = row[col]
                if pd.isna(value):
                    formatted_row.append("N/A")
                elif isinstance(value, (int, float)):
                    if col == 'speedup':
                        formatted_row.append(f"{value:.1f}x")
                    elif col == 'gztool_time':
                        formatted_row.append(f"{value:.4f}s")
                    elif col == 'estimated_linear_time':
                        formatted_row.append(f"{value:.2f}s")
                    elif col == 'position_gb':
                        formatted_row.append(f"{value:.2f}")
                    else:
                        formatted_row.append(str(value))
                else:
                    formatted_row.append(str(value))
            
            markdown_lines.append("| " + " | ".join(formatted_row) + " |")
        
        return "\n".join(markdown_lines)
    
    def create_table_image(self, output_path: str, columns: Optional[List[str]] = None,
                          max_rows: Optional[int] = None, title: str = "Research Data Table"):
        """Create a PNG image of the data table."""
        
        if columns is None:
            columns = [
                'test_id', 'index_point', 'position_gb', 'gztool_time', 
                'estimated_linear_time', 'speedup', 'success'
            ]
        
        # Filter to existing columns
        available_columns = [col for col in columns if col in self.df.columns]
        display_df = self.df[available_columns].copy()
        
        if max_rows:
            display_df = display_df.head(max_rows)
        
        # Format column names for display
        display_df.columns = [col.replace('_', ' ').title() for col in available_columns]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, max(6, len(display_df) * 0.4 + 2)))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table = ax.table(
            cellText=display_df.values,
            colLabels=display_df.columns,
            cellLoc='center',
            loc='center'
        )
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.8)
        
        # Color header row
        for i in range(len(display_df.columns)):
            table[(0, i)].set_facecolor('#2E86AB')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Color alternate rows
        for i in range(1, len(display_df) + 1):
            for j in range(len(display_df.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#F8F9FA')
                else:
                    table[(i, j)].set_facecolor('#FFFFFF')
        
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"✅ Created table image: {output_path}")
    
    def create_summary_visualization(self, output_path: str):
        """Create a comprehensive summary visualization."""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Speedup distribution
        if 'speedup' in self.df.columns:
            ax1.hist(self.df['speedup'], bins=15, alpha=0.7, color='#2E86AB', edgecolor='black')
            ax1.set_xlabel('Speedup (x times faster)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Speedup Distribution')
            ax1.grid(True, alpha=0.3)
            
            # Add statistics
            mean_speedup = self.df['speedup'].mean()
            median_speedup = self.df['speedup'].median()
            ax1.axvline(mean_speedup, color='red', linestyle='--', label=f'Mean: {mean_speedup:.1f}x')
            ax1.axvline(median_speedup, color='orange', linestyle='--', label=f'Median: {median_speedup:.1f}x')
            ax1.legend()
        
        # 2. Access time vs Position
        if 'position_gb' in self.df.columns and 'gztool_time' in self.df.columns:
            ax2.scatter(self.df['position_gb'], self.df['gztool_time'] * 1000, 
                       alpha=0.7, s=50, color='#A23B72')
            ax2.set_xlabel('Position in File (GB)')
            ax2.set_ylabel('Access Time (ms)')
            ax2.set_title('Access Time vs File Position')
            ax2.grid(True, alpha=0.3)
        
        # 3. Performance comparison
        if all(col in self.df.columns for col in ['position_gb', 'gztool_time', 'estimated_linear_time']):
            positions = self.df['position_gb'].values
            gztool_times = self.df['gztool_time'].values
            linear_times = self.df['estimated_linear_time'].values
            
            # Sort by position
            sort_idx = np.argsort(positions)
            positions = positions[sort_idx]
            gztool_times = gztool_times[sort_idx]
            linear_times = linear_times[sort_idx]
            
            ax3.plot(positions, gztool_times, 'o-', label='gztool (actual)', 
                    linewidth=2, markersize=4, color='#2E86AB')
            ax3.plot(positions, linear_times, 's-', label='Linear (estimated)', 
                    linewidth=2, markersize=4, color='#F18F01')
            
            ax3.set_xlabel('Position in File (GB)')
            ax3.set_ylabel('Access Time (seconds)')
            ax3.set_title('Performance Comparison')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax3.set_yscale('log')
        
        # 4. Summary statistics table
        stats = self.generate_summary_stats()
        
        # Create text summary
        summary_text = "Performance Summary:\n\n"
        if 'speedup' in stats:
            summary_text += f"Mean Speedup: {stats['speedup']['mean']:.1f}x\n"
            summary_text += f"Median Speedup: {stats['speedup']['median']:.1f}x\n"
            summary_text += f"Max Speedup: {stats['speedup']['max']:.1f}x\n"
            summary_text += f"Min Speedup: {stats['speedup']['min']:.1f}x\n\n"
        
        if 'access_time' in stats:
            summary_text += f"Mean Access Time: {stats['access_time']['mean_ms']:.1f}ms\n"
            summary_text += f"Access Time Range: {stats['access_time']['min_ms']:.1f}-{stats['access_time']['max_ms']:.1f}ms\n\n"
        
        if 'success_rate' in stats:
            summary_text += f"Success Rate: {stats['success_rate']:.1f}%\n"
            summary_text += f"Total Tests: {len(self.df)}"
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
                fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('Summary Statistics')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"✅ Created summary visualization: {output_path}")
    
    def create_detailed_report(self, output_path: str):
        """Create a detailed markdown report with embedded data."""
        
        stats = self.generate_summary_stats()
        
        report_lines = [
            "# Detailed Research Data Analysis Report",
            "",
            f"**Generated from:** {self.csv_path}",
            f"**Total Records:** {len(self.df)}",
            f"**Analysis Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            ""
        ]
        
        if 'speedup' in stats:
            report_lines.extend([
                f"- **Mean Performance Improvement:** {stats['speedup']['mean']:.1f}x faster than linear access",
                f"- **Median Performance Improvement:** {stats['speedup']['median']:.1f}x faster than linear access",
                f"- **Performance Range:** {stats['speedup']['min']:.1f}x to {stats['speedup']['max']:.1f}x improvement",
            ])
        
        if 'access_time' in stats:
            report_lines.extend([
                f"- **Average Access Time:** {stats['access_time']['mean_ms']:.1f} milliseconds",
                f"- **Access Time Consistency:** ±{stats['access_time']['std_ms']:.1f}ms standard deviation",
            ])
        
        if 'success_rate' in stats:
            report_lines.extend([
                f"- **Reliability:** {stats['success_rate']:.1f}% success rate",
            ])
        
        report_lines.extend([
            "",
            "## Complete Dataset",
            "",
            "### Performance Metrics Table",
            "",
            self.create_markdown_table(),
            "",
            "## Statistical Analysis",
            ""
        ])
        
        if 'speedup' in stats:
            report_lines.extend([
                "### Speedup Performance",
                "",
                "| Statistic | Value |",
                "|-----------|-------|",
                f"| Count | {stats['speedup']['count']} |",
                f"| Mean | {stats['speedup']['mean']:.1f}x |",
                f"| Standard Deviation | {stats['speedup']['std']:.1f}x |",
                f"| Minimum | {stats['speedup']['min']:.1f}x |",
                f"| 25th Percentile | {stats['speedup']['q25']:.1f}x |",
                f"| Median | {stats['speedup']['median']:.1f}x |",
                f"| 75th Percentile | {stats['speedup']['q75']:.1f}x |",
                f"| Maximum | {stats['speedup']['max']:.1f}x |",
                ""
            ])
        
        if 'access_time' in stats:
            report_lines.extend([
                "### Access Time Performance",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Mean Access Time | {stats['access_time']['mean_ms']:.2f}ms |",
                f"| Standard Deviation | {stats['access_time']['std_ms']:.2f}ms |",
                f"| Minimum Access Time | {stats['access_time']['min_ms']:.2f}ms |",
                f"| Maximum Access Time | {stats['access_time']['max_ms']:.2f}ms |",
                ""
            ])
        
        report_lines.extend([
            "## Data Refresh Commands",
            "",
            "To regenerate this analysis with updated data:",
            "",
            "```bash",
            "# Update graphs and data",
            "python test-gztool.py --num-tests 30 --csv-output research_results.csv --graph-output research_graphs",
            "",
            "# Regenerate this report",
            "python csv_to_formats.py research_results.csv --markdown-report updated_report.md",
            "",
            "# Create new table images",
            "python csv_to_formats.py research_results.csv --table-image updated_table.png",
            "```",
            "",
            "---",
            "*Report generated automatically from research data*"
        ])
        
        # Write report
        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✅ Created detailed report: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert CSV research data to various formats")
    parser.add_argument("csv_file", help="Path to CSV file to analyze")
    parser.add_argument("--markdown-table", help="Output markdown table to file")
    parser.add_argument("--table-image", help="Output table as PNG image")
    parser.add_argument("--summary-viz", help="Output summary visualization PNG")
    parser.add_argument("--markdown-report", help="Output detailed markdown report")
    parser.add_argument("--max-rows", type=int, default=15, 
                       help="Maximum rows to include in tables (default: 15)")
    parser.add_argument("--columns", nargs="+", 
                       help="Specific columns to include in table output")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"❌ CSV file not found: {args.csv_file}")
        return 1
    
    # Initialize analyzer
    analyzer = CSVAnalyzer(args.csv_file)
    
    print(f"📊 Analyzing CSV data: {args.csv_file}")
    print(f"   Records: {len(analyzer.df)}")
    print(f"   Columns: {list(analyzer.df.columns)}")
    
    # Generate outputs based on arguments
    if args.markdown_table:
        markdown_table = analyzer.create_markdown_table(
            columns=args.columns, 
            max_rows=args.max_rows
        )
        with open(args.markdown_table, 'w') as f:
            f.write(markdown_table)
        print(f"✅ Created markdown table: {args.markdown_table}")
    
    if args.table_image:
        analyzer.create_table_image(
            args.table_image,
            columns=args.columns,
            max_rows=args.max_rows
        )
    
    if args.summary_viz:
        analyzer.create_summary_visualization(args.summary_viz)
    
    if args.markdown_report:
        analyzer.create_detailed_report(args.markdown_report)
    
    # If no specific output requested, show summary
    if not any([args.markdown_table, args.table_image, args.summary_viz, args.markdown_report]):
        print("\n📈 Summary Statistics:")
        stats = analyzer.generate_summary_stats()
        
        if 'speedup' in stats:
            print(f"   Speedup: {stats['speedup']['mean']:.1f}x ± {stats['speedup']['std']:.1f}x")
            print(f"   Range: {stats['speedup']['min']:.1f}x - {stats['speedup']['max']:.1f}x")
        
        if 'access_time' in stats:
            print(f"   Access Time: {stats['access_time']['mean_ms']:.1f}ms ± {stats['access_time']['std_ms']:.1f}ms")
        
        print("\n💡 Use --help to see output format options")
    
    return 0


if __name__ == "__main__":
    exit(main()) 