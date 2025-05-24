#!/usr/bin/env python3
"""
Practical demonstration of gztool for HTTP range requests.

This script demonstrates the key concepts:
1. Creating indexes for gzip files
2. Understanding index structure
3. Mapping uncompressed positions to compressed positions
4. Simulating HTTP range requests
5. Extracting specific ranges
"""

import os
import subprocess
import requests
import json
from typing import Tuple, Optional, Dict
import argparse


class GzToolRangeDemo:
    """Practical demonstration of gztool for HTTP range requests."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
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
    
    def create_index(self, gzip_file: str, span_mb: int = 10) -> Tuple[bool, str]:
        """Create an index for a gzip file."""
        index_file = gzip_file.replace('.gz', '.gzi')
        command = ["gztool", f"-s{span_mb}", "-i", gzip_file]
        
        exit_code, stdout, stderr = self._run_command(command)
        
        if exit_code == 0:
            print(f"✅ Index created successfully: {index_file}")
            return True, index_file
        else:
            print(f"❌ Failed to create index: {stderr}")
            return False, ""
    
    def get_index_info(self, index_file: str) -> Dict:
        """Get detailed information about an index file."""
        command = ["gztool", "-l", index_file]  # Use simple -l instead of -ll
        exit_code, stdout, stderr = self._run_command(command)
        
        if exit_code != 0:
            return {}
        
        info = {}
        lines = stdout.split('\n')
        
        for line in lines:
            if 'Size of index file' in line:
                # Extract index size - look for pattern like "2464080 Bytes"
                parts = line.split('(')
                for part in parts:
                    if 'Bytes' in part:
                        bytes_part = part.split('Bytes')[0].strip().replace(',', '')
                        try:
                            info['index_size_bytes'] = int(bytes_part)
                            break
                        except ValueError:
                            continue
            elif 'Number of index points' in line:
                info['index_points'] = int(line.split(':')[1].strip())
            elif 'Size of uncompressed file' in line:
                # Extract uncompressed size - look for pattern like "4510998952 Bytes"
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
                # Extract compressed size from this line
                parts = line.split('(')
                for part in parts:
                    if 'Bytes' in part and '%' not in part:  # Avoid the percentage part
                        bytes_part = part.split('Bytes')[0].strip().replace(',', '')
                        try:
                            info['compressed_size_bytes'] = int(bytes_part)
                            break
                        except ValueError:
                            continue
        
        return info
    
    def extract_range(self, gzip_file: str, start_byte: int, num_bytes: int) -> Tuple[bool, str]:
        """Extract a specific byte range from a gzip file."""
        command = ["gztool", f"-b{start_byte}", f"-r{num_bytes}", gzip_file]
        
        exit_code, stdout, stderr = self._run_command(command)
        
        if exit_code == 0:
            print(f"✅ Extracted {num_bytes} bytes starting from position {start_byte}")
            return True, stdout
        else:
            print(f"❌ Failed to extract range: {stderr}")
            return False, ""
    
    def calculate_compression_efficiency(self, info: Dict) -> Dict:
        """Calculate compression statistics."""
        if not info:
            return {}
        
        compressed_size = info.get('compressed_size_bytes', 0)
        uncompressed_size = info.get('uncompressed_size_bytes', 0)
        index_points = info.get('index_points', 0)
        
        if uncompressed_size == 0:
            return {}
        
        compression_ratio = compressed_size / uncompressed_size
        space_savings = 1 - compression_ratio
        
        # Calculate average span between index points
        avg_span_mb = (uncompressed_size / (1024 * 1024)) / index_points if index_points > 0 else 0
        
        return {
            'compression_ratio': compression_ratio,
            'space_savings_percent': space_savings * 100,
            'avg_span_mb': avg_span_mb,
            'compressed_mb': compressed_size / (1024 * 1024),
            'uncompressed_mb': uncompressed_size / (1024 * 1024)
        }
    
    def estimate_http_range(self, info: Dict, target_uncompressed_start: int, 
                          target_uncompressed_length: int) -> Dict:
        """Estimate the HTTP range needed for a given uncompressed range."""
        if not info:
            return {}
        
        compression_ratio = info.get('compressed_size_bytes', 1) / info.get('uncompressed_size_bytes', 1)
        
        # Estimate compressed start position
        estimated_comp_start = int(target_uncompressed_start * compression_ratio)
        
        # Use a conservative buffer to ensure we get enough data
        # Real implementation would use the actual index points
        buffer_factor = 2.0  # 100% buffer
        estimated_comp_length = int(target_uncompressed_length * compression_ratio * buffer_factor)
        
        return {
            'estimated_compressed_start': estimated_comp_start,
            'estimated_compressed_length': estimated_comp_length,
            'estimated_compressed_end': estimated_comp_start + estimated_comp_length,
            'compression_ratio': compression_ratio,
            'buffer_factor': buffer_factor
        }


def demonstrate_with_local_file():
    """Demonstrate gztool functionality with local test file."""
    print("🔬 === Local File Demonstration ===")
    
    demo = GzToolRangeDemo(verbose=True)
    gzip_file = "data/test-file.gz"
    
    if not os.path.exists(gzip_file):
        print(f"❌ Test file {gzip_file} not found!")
        return
    
    print(f"📁 Using test file: {gzip_file}")
    file_size = os.path.getsize(gzip_file)
    print(f"📊 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    # Step 1: Create or use existing index
    print("\n🔧 Step 1: Creating index...")
    success, index_file = demo.create_index(gzip_file, span_mb=5)
    if not success:
        return
    
    # Step 2: Analyze index
    print("\n📊 Step 2: Analyzing index...")
    info = demo.get_index_info(index_file)
    stats = demo.calculate_compression_efficiency(info)
    
    print("Index Information:")
    print(f"  • Index points: {info.get('index_points', 'N/A')}")
    print(f"  • Uncompressed size: {stats.get('uncompressed_mb', 0):.2f} MB")
    print(f"  • Compressed size: {stats.get('compressed_mb', 0):.2f} MB")
    print(f"  • Compression ratio: {stats.get('compression_ratio', 0):.4f}")
    print(f"  • Space savings: {stats.get('space_savings_percent', 0):.1f}%")
    print(f"  • Avg span between index points: {stats.get('avg_span_mb', 0):.2f} MB")
    
    # Step 3: Extract sample ranges
    print("\n🎯 Step 3: Extracting sample ranges...")
    
    uncompressed_size = info.get('uncompressed_size_bytes', 0)
    if uncompressed_size == 0:
        print("❌ Could not determine uncompressed size")
        return
    
    # Define some interesting positions to extract
    positions = [
        {"name": "Beginning", "start": 1000, "length": 500},
        {"name": "25% mark", "start": uncompressed_size // 4, "length": 1000},
        {"name": "50% mark", "start": uncompressed_size // 2, "length": 1000},
        {"name": "75% mark", "start": (uncompressed_size * 3) // 4, "length": 1000},
    ]
    
    for pos in positions:
        print(f"\n  🔍 Extracting from {pos['name']}:")
        print(f"     Position: {pos['start']:,} (length: {pos['length']})")
        
        # Estimate HTTP range that would be needed
        range_info = demo.estimate_http_range(info, pos['start'], pos['length'])
        
        print(f"     Estimated HTTP range: {range_info.get('estimated_compressed_start', 0):,}-{range_info.get('estimated_compressed_end', 0):,}")
        print(f"     Estimated compressed bytes needed: {range_info.get('estimated_compressed_length', 0):,}")
        
        # Extract the actual data
        success, content = demo.extract_range(gzip_file, pos['start'], pos['length'])
        
        if success:
            # Show a preview of the content
            preview = content[:100].replace('\n', '\\n').replace('\r', '\\r')
            print(f"     Content preview: {preview}...")
        
        print(f"     ✅ Extraction completed")


def demonstrate_http_workflow():
    """Demonstrate the HTTP range request workflow conceptually."""
    print("\n🌐 === HTTP Range Request Workflow ===")
    
    print("""
The HTTP range request workflow with gztool would work as follows:

1. 📥 INITIAL SETUP (one-time):
   • Download the complete gzip file
   • Create an index using: gztool -s10 -i file.gz
   • Store the index file for future use

2. 🎯 FOR EACH RANGE REQUEST:
   • Determine target uncompressed byte range
   • Use index to find corresponding compressed byte range
   • Send HTTP Range request: Range: bytes=start-end
   • Download only the needed compressed chunk
   • Use gztool to decompress just that chunk

3. 💡 KEY BENEFITS:
   • Only download ~1-5% of the original file size for small ranges
   • Near-instant access to any part of the gzip file
   • No need to decompress the entire file
   • Index files are small (typically <1% of original size)
    """)
    
    # Show a practical example with the remote file
    remote_url = "https://lifewise.sapphiremrfhub.com/mrfs/202505/MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gz"
    
    print(f"\n📋 EXAMPLE with remote file:")
    print(f"   URL: {remote_url}")
    
    try:
        # Get file size without downloading
        response = requests.head(remote_url, timeout=10)
        if response.status_code == 200:
            file_size = int(response.headers.get('content-length', 0))
            print(f"   Remote file size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            
            # Simulate what we'd do
            target_position = file_size // 2  # Middle of compressed file (rough estimate)
            target_length = 50000  # 50KB of uncompressed data
            
            print(f"\n   🎯 To extract 50KB from middle of uncompressed data:")
            print(f"      1. Estimate compressed position: ~{target_position:,}")
            print(f"      2. HTTP Range request: bytes={target_position}-{target_position + target_length}")
            print(f"      3. Download: ~{target_length:,} bytes instead of {file_size:,} bytes")
            print(f"      4. Savings: {((file_size - target_length) / file_size * 100):.1f}% bandwidth saved")
        
        else:
            print(f"   ❌ Could not access remote file: HTTP {response.status_code}")
    
    except Exception as e:
        print(f"   ⚠️  Could not check remote file: {e}")


def main():
    """Main demonstration function."""
    parser = argparse.ArgumentParser(description="Practical gztool HTTP range demonstration")
    parser.add_argument("--demo", choices=["local", "workflow", "both"], 
                       default="both", help="Which demo to run")
    
    args = parser.parse_args()
    
    print("🚀 gztool HTTP Range Request Demonstration")
    print("=" * 60)
    
    if args.demo in ["local", "both"]:
        demonstrate_with_local_file()
    
    if args.demo in ["workflow", "both"]:
        demonstrate_http_workflow()
    
    print("\n" + "=" * 60)
    print("✅ Demonstration completed!")
    
    print("\n💡 Key Takeaways:")
    print("• gztool enables random access to gzip files")
    print("• Index files are small and enable efficient range requests")
    print("• HTTP Range requests can dramatically reduce bandwidth usage")
    print("• Perfect for accessing specific portions of large compressed files")


if __name__ == "__main__":
    main() 