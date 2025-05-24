#!/usr/bin/env python3
"""
HTTP Range Request Demo for gztool

Demonstrates downloading specific byte ranges from the remote gzip file.
"""

import requests
import argparse
import sys
from typing import Tuple


def get_file_info(url: str) -> Tuple[bool, int]:
    """Get basic information about the remote file."""
    try:
        print(f"🔍 Checking file: {url}")
        response = requests.head(url, timeout=10)
        
        if response.status_code == 200:
            size = int(response.headers.get('content-length', 0))
            print(f"✅ File accessible, size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
            
            # Check if server supports range requests
            accept_ranges = response.headers.get('accept-ranges', '').lower()
            if accept_ranges == 'bytes':
                print("✅ Server supports HTTP Range requests")
            else:
                print("⚠️  Server may not support HTTP Range requests")
            
            return True, size
        else:
            print(f"❌ Cannot access file: HTTP {response.status_code}")
            return False, 0
    
    except Exception as e:
        print(f"❌ Error accessing file: {e}")
        return False, 0


def download_range(url: str, start: int, end: int, output_file: str = None) -> bool:
    """Download a specific byte range from the URL."""
    try:
        headers = {'Range': f'bytes={start}-{end}'}
        print(f"🌐 Downloading bytes {start:,}-{end:,} ({(end-start+1):,} bytes)")
        
        response = requests.get(url, headers=headers, stream=True)
        
        if response.status_code == 206:  # Partial Content
            content_length = int(response.headers.get('content-length', 0))
            
            if output_file:
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ Downloaded {content_length:,} bytes to {output_file}")
            else:
                content = response.content
                print(f"✅ Downloaded {len(content):,} bytes")
                print(f"📄 Content preview (first 100 bytes):")
                print(content[:100])
            
            return True
        
        elif response.status_code == 200:
            print("⚠️  Server returned full file instead of range (range not supported)")
            return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.reason}")
            return False
    
    except Exception as e:
        print(f"❌ Error downloading range: {e}")
        return False


def demonstrate_ranges(url: str, file_size: int):
    """Demonstrate downloading various ranges from the file."""
    print("\n🎯 Demonstrating HTTP Range Requests")
    print("=" * 50)
    
    # Define some interesting ranges to download
    ranges = [
        {
            "name": "First 1KB (file header)",
            "start": 0,
            "length": 1024,
            "description": "Contains gzip header and beginning of compressed data"
        },
        {
            "name": "Small chunk from beginning",
            "start": 1024,
            "length": 8192,  # 8KB
            "description": "Early compressed data"
        },
        {
            "name": "Chunk from middle",
            "start": file_size // 2,
            "length": 4096,  # 4KB
            "description": "Middle portion of compressed data"
        },
        {
            "name": "End of file",
            "start": max(0, file_size - 1024),
            "length": 1024,
            "description": "Contains gzip trailer with CRC and size"
        }
    ]
    
    for i, range_info in enumerate(ranges, 1):
        start = range_info["start"]
        length = range_info["length"]
        end = min(start + length - 1, file_size - 1)
        
        print(f"\n{i}. {range_info['name']}")
        print(f"   {range_info['description']}")
        print(f"   Range: {start:,}-{end:,} bytes")
        
        # Download to a temporary file
        output_file = f"range_{i}_bytes_{start}_{end}.gz"
        success = download_range(url, start, end, output_file)
        
        if success:
            bandwidth_saved = ((file_size - (end - start + 1)) / file_size) * 100
            print(f"   💾 Saved to: {output_file}")
            print(f"   📊 Bandwidth saved: {bandwidth_saved:.1f}%")
        
        print()


def main():
    parser = argparse.ArgumentParser(description="HTTP Range Request demonstration with gztool")
    parser.add_argument(
        "--url", 
        default="https://lifewise.sapphiremrfhub.com/mrfs/202505/MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gz",
        help="URL of the gzip file to test"
    )
    parser.add_argument(
        "--range", 
        help="Specific range to download (format: start-end)"
    )
    parser.add_argument(
        "--output", 
        help="Output file for downloaded range"
    )
    parser.add_argument(
        "--demo", 
        action="store_true",
        help="Run demonstration with predefined ranges"
    )
    
    args = parser.parse_args()
    
    print("🚀 HTTP Range Request Demo for gztool")
    print("=" * 60)
    
    # Get file information
    success, file_size = get_file_info(args.url)
    if not success:
        sys.exit(1)
    
    # Handle specific range request
    if args.range:
        try:
            if '-' in args.range:
                start, end = map(int, args.range.split('-'))
            else:
                # Single byte position, download 1KB from there
                start = int(args.range)
                end = start + 1023
            
            if end >= file_size:
                end = file_size - 1
            
            success = download_range(args.url, start, end, args.output)
            if not success:
                sys.exit(1)
        
        except ValueError:
            print("❌ Invalid range format. Use: start-end or just start")
            sys.exit(1)
    
    # Run demonstration
    elif args.demo:
        demonstrate_ranges(args.url, file_size)
        
        print("🎯 Key Insights from this Demo:")
        print("• HTTP Range requests work with this server")
        print("• You can download small chunks instead of the full 96MB file")
        print("• Gzip headers and trailers are accessible via ranges")
        print("• This enables efficient random access patterns")
        print("\n💡 Next Steps:")
        print("• Use gztool to create an index of the complete file")
        print("• Map uncompressed positions to compressed ranges")
        print("• Download only the compressed ranges you need")
        print("• Use gztool to extract specific uncompressed data")
    
    else:
        print("\n💡 Usage Examples:")
        print("# Download first 1KB:")
        print(f"python {sys.argv[0]} --range 0-1023 --output header.gz")
        print("\n# Download from middle:")
        print(f"python {sys.argv[0]} --range 50000000-50010000")
        print("\n# Run full demonstration:")
        print(f"python {sys.argv[0]} --demo")


if __name__ == "__main__":
    main() 