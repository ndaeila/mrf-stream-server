#!/usr/bin/env python3
"""
Enhanced gztool testing suite for research analysis.

This script provides comprehensive testing and data collection capabilities
for analyzing gztool performance across multiple access patterns.
"""

import os
import subprocess
import requests
import tempfile
import json
import time
import random
import csv
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import Tuple, Optional, List, Dict
import numpy as np
from datetime import datetime


class GzToolResearchSuite:
    """Enhanced research suite for gztool performance analysis."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        
    def _run_command(self, command: list) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        if self.verbose:
            print(f"📋 Running: {' '.join(command)}")
        
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        
        return result.returncode, result.stdout, result.stderr
    
    def get_file_info(self, gzip_file: str) -> Dict:
        """Get comprehensive file information."""
        index_file = gzip_file.replace('.gz', '.gzi')
        
        if not os.path.exists(index_file):
            print(f"Creating index for {gzip_file}...")
            self._run_command(["gztool", "-s5", "-i", gzip_file])
        
        # Get index information
        command = ["gztool", "-l", index_file]
        exit_code, stdout, stderr = self._run_command(command)
        
        info = {}
        if exit_code == 0:
            lines = stdout.split('\n')
            for line in lines:
                if 'Number of index points' in line:
                    info['index_points'] = int(line.split(':')[1].strip())
                elif 'Size of uncompressed file' in line:
                    parts = line.split('(')
                    for part in parts:
                        if 'Bytes' in part:
                            bytes_part = part.split('Bytes')[0].strip().replace(',', '')
                            try:
                                info['uncompressed_size_bytes'] = int(bytes_part)
                                break
                            except ValueError:
                                continue
                elif 'Guessed gzip file name' in line and 'Bytes' in line:
                    parts = line.split('(')
                    for part in parts:
                        if 'Bytes' in part and '%' not in part:
                            bytes_part = part.split('Bytes')[0].strip().replace(',', '')
                            try:
                                info['compressed_size_bytes'] = int(bytes_part)
                                break
                            except ValueError:
                                continue
        
        return info
    
    def calculate_position(self, index_point: int, total_points: int, total_size: int) -> int:
        """Calculate byte position for a given index point."""
        return int((index_point / total_points) * total_size)
    
    def benchmark_gztool_access(self, gzip_file: str, position: int, length: int) -> Dict:
        """Benchmark gztool access for a specific position."""
        start_time = time.time()
        
        cmd = ["gztool", f"-b{position}", f"-r{length}", gzip_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        end_time = time.time()
        access_time = end_time - start_time
        
        success = result.returncode == 0
        data_length = len(result.stdout) if success else 0
        
        return {
            'position': position,
            'length': length,
            'access_time': access_time,
            'success': success,
            'data_length': data_length,
            'data_sample': result.stdout[:100] if success else None
        }
    
    def estimate_linear_access_time(self, position: int, read_speed_mbs: float = 200.0) -> float:
        """Estimate linear access time based on position and read speed."""
        return (position / (1024 * 1024)) / read_speed_mbs
    
    def run_single_test(self, gzip_file: str, index_point: int = None, extract_length: int = 1000) -> Dict:
        """Run a single test at specified or random index point."""
        info = self.get_file_info(gzip_file)
        
        if index_point is None:
            index_point = random.randint(1, info['index_points'] - 1)
        
        position = self.calculate_position(index_point, info['index_points'], info['uncompressed_size_bytes'])
        
        # Benchmark gztool access
        gztool_result = self.benchmark_gztool_access(gzip_file, position, extract_length)
        
        # Estimate linear access time
        linear_time = self.estimate_linear_access_time(position)
        
        # Calculate metrics
        speedup = linear_time / gztool_result['access_time'] if gztool_result['access_time'] > 0 else 0
        compression_ratio = info.get('compressed_size_bytes', 1) / info.get('uncompressed_size_bytes', 1)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_id': len(self.test_results) + 1,
            'index_point': index_point,
            'position': position,
            'position_gb': position / (1024**3),
            'extract_length': extract_length,
            'gztool_time': gztool_result['access_time'],
            'estimated_linear_time': linear_time,
            'speedup': speedup,
            'success': gztool_result['success'],
            'data_length': gztool_result['data_length'],
            'compression_ratio': compression_ratio,
            'file_size_gb': info.get('uncompressed_size_bytes', 0) / (1024**3),
            'compressed_size_mb': info.get('compressed_size_bytes', 0) / (1024**2),
            'data_sample': gztool_result['data_sample']
        }
        
        self.test_results.append(result)
        return result
    
    def run_multiple_tests(self, gzip_file: str, num_tests: int, extract_length: int = 1000) -> List[Dict]:
        """Run multiple tests with random index points."""
        print(f"🧪 Running {num_tests} tests with random index points...")
        
        results = []
        for i in range(num_tests):
            if self.verbose:
                print(f"Test {i+1}/{num_tests}", end=" ")
            
            result = self.run_single_test(gzip_file, extract_length=extract_length)
            results.append(result)
            
            if self.verbose:
                print(f"✅ Index {result['index_point']} ({result['gztool_time']:.3f}s, {result['speedup']:.0f}x speedup)")
        
        return results
    
    def save_results_csv(self, output_path: str):
        """Save test results to CSV file."""
        if not self.test_results:
            print("❌ No test results to save")
            return False
        
        fieldnames = [
            'timestamp', 'test_id', 'index_point', 'position', 'position_gb',
            'extract_length', 'gztool_time', 'estimated_linear_time', 'speedup',
            'success', 'data_length', 'compression_ratio', 'file_size_gb',
            'compressed_size_mb', 'data_sample'
        ]
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.test_results)
        
        print(f"✅ Saved {len(self.test_results)} test results to {output_path}")
        return True
    
    def generate_performance_graphs(self, output_dir: str):
        """Generate comprehensive performance analysis graphs."""
        if not self.test_results:
            print("❌ No test results to plot")
            return
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(self.test_results)
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # 1. Speedup vs Position
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        ax1.scatter(df['position_gb'], df['speedup'], alpha=0.7, s=50)
        ax1.set_xlabel('Position in File (GB)')
        ax1.set_ylabel('Speedup (x times faster than linear)')
        ax1.set_title('gztool Speedup vs File Position')
        ax1.grid(True, alpha=0.3)
        
        # 2. Access Time Distribution
        ax2.hist(df['gztool_time'] * 1000, bins=20, alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Access Time (milliseconds)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('gztool Access Time Distribution')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/performance_overview.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Performance Comparison Chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create comparison data
        positions = df['position_gb'].values
        gztool_times = df['gztool_time'].values
        linear_times = df['estimated_linear_time'].values
        
        # Sort by position for cleaner lines
        sort_idx = np.argsort(positions)
        positions = positions[sort_idx]
        gztool_times = gztool_times[sort_idx]
        linear_times = linear_times[sort_idx]
        
        ax.plot(positions, gztool_times, 'o-', label='gztool (actual)', linewidth=2, markersize=4)
        ax.plot(positions, linear_times, 's-', label='Linear streaming (estimated)', linewidth=2, markersize=4)
        
        ax.set_xlabel('Position in File (GB)')
        ax.set_ylabel('Access Time (seconds)')
        ax.set_title('Performance Comparison: gztool vs Linear Access')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/performance_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Speedup Statistics
        fig, ax = plt.subplots(figsize=(10, 6))
        
        speedup_stats = df['speedup'].describe()
        
        # Box plot of speedups
        ax.boxplot([df['speedup']], labels=['gztool vs Linear'])
        ax.set_ylabel('Speedup (x times faster)')
        ax.set_title('gztool Performance Speedup Distribution')
        ax.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = f"""Statistics:
        Mean: {speedup_stats['mean']:.1f}x
        Median: {speedup_stats['50%']:.1f}x
        Min: {speedup_stats['min']:.1f}x
        Max: {speedup_stats['max']:.1f}x"""
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/speedup_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Generated performance graphs in {output_dir}/")
        
        # Also save a summary plot as DataFrame to PNG
        self.save_dataframe_as_image(df, f"{output_dir}/results_table.png")
    
    def save_dataframe_as_image(self, df: pd.DataFrame, output_path: str):
        """Convert DataFrame to a formatted table image."""
        # Select key columns for the table
        display_df = df[[
            'test_id', 'index_point', 'position_gb', 'gztool_time', 
            'estimated_linear_time', 'speedup', 'success'
        ]].copy()
        
        # Round numerical columns
        display_df['position_gb'] = display_df['position_gb'].round(2)
        display_df['gztool_time'] = display_df['gztool_time'].round(4)
        display_df['estimated_linear_time'] = display_df['estimated_linear_time'].round(2)
        display_df['speedup'] = display_df['speedup'].round(1)
        
        # Rename columns for display
        display_df.columns = [
            'Test ID', 'Index Point', 'Position (GB)', 'gztool Time (s)', 
            'Linear Time (s)', 'Speedup (x)', 'Success'
        ]
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(14, max(8, len(display_df) * 0.3 + 2)))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table = ax.table(cellText=display_df.values, colLabels=display_df.columns,
                        cellLoc='center', loc='center')
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Color header row
        for i in range(len(display_df.columns)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Color alternate rows
        for i in range(1, len(display_df) + 1):
            for j in range(len(display_df.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.title('gztool Performance Test Results', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved results table as image: {output_path}")
    
    def generate_summary_statistics(self) -> Dict:
        """Generate comprehensive summary statistics."""
        if not self.test_results:
            return {}
        
        df = pd.DataFrame(self.test_results)
        
        stats = {
            'total_tests': len(self.test_results),
            'successful_tests': df['success'].sum(),
            'success_rate': df['success'].mean() * 100,
            'avg_gztool_time': df['gztool_time'].mean(),
            'avg_speedup': df['speedup'].mean(),
            'median_speedup': df['speedup'].median(),
            'min_speedup': df['speedup'].min(),
            'max_speedup': df['speedup'].max(),
            'std_speedup': df['speedup'].std(),
            'avg_position_gb': df['position_gb'].mean(),
            'file_size_gb': df['file_size_gb'].iloc[0] if len(df) > 0 else 0,
            'compression_ratio': df['compression_ratio'].iloc[0] if len(df) > 0 else 0
        }
        
        return stats


def main():
    parser = argparse.ArgumentParser(description="Enhanced gztool research testing suite")
    parser.add_argument("--file", default="data/test-file.gz", 
                       help="Gzip file to test (default: data/test-file.gz)")
    parser.add_argument("--random", action="store_true",
                       help="Run single test at random index point")
    parser.add_argument("--index-point", type=int,
                       help="Specific index point to test")
    parser.add_argument("--num-tests", type=int, default=1,
                       help="Number of tests to run (default: 1)")
    parser.add_argument("--extract-length", type=int, default=1000,
                       help="Number of bytes to extract per test (default: 1000)")
    parser.add_argument("--csv-output", 
                       help="Output CSV file path for results")
    parser.add_argument("--graph-output", 
                       help="Output directory for graph images")
    parser.add_argument("--verbose", action="store_true", default=True,
                       help="Verbose output (default: True)")
    
    args = parser.parse_args()
    
    # Initialize test suite
    suite = GzToolResearchSuite(verbose=args.verbose)
    
    print("🧬 gztool Research Testing Suite")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return 1
    
    # Run tests
    if args.num_tests == 1:
        # Single test
        index_point = args.index_point if not args.random else None
        result = suite.run_single_test(args.file, index_point, args.extract_length)
        
        print(f"\n📊 Single Test Results:")
        print(f"   Index Point: {result['index_point']}")
        print(f"   Position: {result['position']:,} bytes ({result['position_gb']:.2f} GB)")
        print(f"   gztool Time: {result['gztool_time']:.4f} seconds")
        print(f"   Estimated Linear Time: {result['estimated_linear_time']:.2f} seconds")
        print(f"   Speedup: {result['speedup']:.1f}x")
        print(f"   Data Sample: {result['data_sample'][:100]}...")
    
    else:
        # Multiple tests
        results = suite.run_multiple_tests(args.file, args.num_tests, args.extract_length)
        
        # Generate summary statistics
        stats = suite.generate_summary_statistics()
        
        print(f"\n📊 Test Results Summary ({args.num_tests} tests):")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")
        print(f"   Average gztool Time: {stats['avg_gztool_time']:.4f} seconds")
        print(f"   Average Speedup: {stats['avg_speedup']:.1f}x")
        print(f"   Speedup Range: {stats['min_speedup']:.1f}x - {stats['max_speedup']:.1f}x")
        print(f"   Median Speedup: {stats['median_speedup']:.1f}x")
    
    # Save CSV if requested
    if args.csv_output:
        suite.save_results_csv(args.csv_output)
    
    # Generate graphs if requested
    if args.graph_output:
        suite.generate_performance_graphs(args.graph_output)
    
    print("\n✅ Testing completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())

