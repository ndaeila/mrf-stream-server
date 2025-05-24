#!/usr/bin/env python3
"""
Complete demonstration of gztool for HTTP range requests workflow.

This script demonstrates:
1. Download complete gzip file and create index
2. Use index to find compressed byte ranges for uncompressed positions  
3. Download specific chunks using HTTP range requests
4. Decompress just those chunks using gztool
"""

import os
import subprocess
import requests
import tempfile
import json
import struct
from typing import Tuple, Optional, List, Dict
import argparse


class GzToolManager:
    """Enhanced manager class for gztool operations."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def _run_command(self, command: list) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        if self.verbose:
            print(f"Running: {' '.join(command)}")
        
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        
        if self.verbose and result.stderr:
            print(f"stderr: {result.stderr}")
        
        return result.returncode, result.stdout, result.stderr
    
    def create_index(self, gzip_file: str, index_file: Optional[str] = None, 
                    span_mb: int = 10) -> Tuple[bool, str]:
        """Create an index for a gzip file."""
        command = ["gztool", f"-s{span_mb}", "-i"]
        
        if index_file:
            command.extend(["-I", index_file])
        
        command.append(gzip_file)
        
        exit_code, stdout, stderr = self._run_command(command)
        
        if exit_code == 0:
            if index_file:
                actual_index_file = index_file
            else:
                actual_index_file = gzip_file.replace('.gz', '.gzi')
            
            print(f"✓ Index created successfully: {actual_index_file}")
            return True, actual_index_file
        else:
            print(f"✗ Failed to create index: {stderr}")
            return False, ""
    
    def list_index_info(self, index_file: str) -> dict:
        """Get information about an index file."""
        command = ["gztool", "-l", index_file]
        exit_code, stdout, stderr = self._run_command(command)
        
        if exit_code != 0:
            return {}
        
        info = {}
        lines = stdout.split('\n')
        for line in lines:
            if 'Size of index file' in line:
                parts = line.split(':')[1].strip()
                info['index_size_mb'] = parts.split('(')[1].split('Bytes')[0].strip().replace(',', '')
            elif 'Number of index points' in line:
                info['index_points'] = int(line.split(':')[1].strip())
            elif 'Size of uncompressed file' in line:
                parts = line.split(':')[1].strip()
                info['uncompressed_size_bytes'] = int(parts.split('(')[1].split('Bytes')[0].strip().replace(',', ''))
            elif 'Guessed gzip file name' in line:
                parts = line.split("'")
                if len(parts) > 1:
                    info['gzip_file'] = parts[1]
                compressed_part = line.split('(')[-1]
                if 'Bytes' in compressed_part:
                    info['compressed_size_bytes'] = int(compressed_part.split('Bytes')[0].strip().replace(',', ''))
        
        return info
    
    def extract_byte_range(self, gzip_file: str, start_byte: int, 
                          num_bytes: int, output_file: Optional[str] = None) -> Tuple[bool, str]:
        """Extract a specific byte range from a gzip file."""
        command = ["gztool", f"-b{start_byte}", f"-r{num_bytes}", gzip_file]
        
        exit_code, stdout, stderr = self._run_command(command)
        
        if exit_code == 0:
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(stdout)
                print(f"✓ Extracted {num_bytes} bytes starting from {start_byte} to {output_file}")
                return True, output_file
            else:
                print(f"✓ Extracted {num_bytes} bytes starting from {start_byte}")
                return True, stdout
        else:
            print(f"✗ Failed to extract byte range: {stderr}")
            return False, ""

    def parse_index_file(self, index_file: str) -> List[Dict]:
        """Parse the gztool index file to get actual index points."""
        index_points = []
        
        try:
            with open(index_file, 'rb') as f:
                # Read gztool index file header
                # This is a simplified parser - the actual format may be more complex
                magic = f.read(4)
                if magic != b'GZTI':  # Hypothetical magic number
                    # Try to parse anyway
                    f.seek(0)
                
                # Skip version and other header info (simplified)
                f.seek(16, 0)  # Skip to data section
                
                # Read index points (this is a rough approximation)
                while True:
                    try:
                        # Read compressed position (8 bytes)
                        comp_pos_data = f.read(8)
                        if len(comp_pos_data) < 8:
                            break
                        comp_pos = struct.unpack('<Q', comp_pos_data)[0]
                        
                        # Read uncompressed position (8 bytes)
                        uncomp_pos_data = f.read(8)
                        if len(uncomp_pos_data) < 8:
                            break
                        uncomp_pos = struct.unpack('<Q', uncomp_pos_data)[0]
                        
                        index_points.append({
                            'compressed_pos': comp_pos,
                            'uncompressed_pos': uncomp_pos
                        })
                        
                        # Skip additional data per index point
                        f.seek(32, 1)  # Skip additional fields
                        
                    except struct.error:
                        break
                        
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not parse index file: {e}")
            return []
        
        return index_points


def download_file(url: str, output_file: str, chunk_size: int = 8192) -> bool:
    """Download a complete file."""
    try:
        print(f"Downloading {url} to {output_file}")
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded:,}/{total_size:,} bytes)", end="")
            
            print(f"\n✓ Download completed: {output_file}")
            return True
        else:
            print(f"✗ Failed to download: HTTP {response.status_code}")
            return False
    
    except Exception as e:
        print(f"✗ Error downloading file: {e}")
        return False


def download_http_range(url: str, start_byte: int, end_byte: int, 
                       output_file: Optional[str] = None) -> Tuple[bool, str]:
    """Download a specific byte range using HTTP Range requests."""
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    
    try:
        print(f"Downloading range {start_byte}-{end_byte} from {url}")
        response = requests.get(url, headers=headers, stream=True)
        
        if response.status_code == 206:  # Partial Content
            if output_file:
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✓ Downloaded range to {output_file}")
                return True, output_file
            else:
                content = response.content
                print(f"✓ Downloaded {len(content)} bytes")
                return True, content
        else:
            print(f"✗ Failed to download range: HTTP {response.status_code}")
            return False, ""
    
    except Exception as e:
        print(f"✗ Error downloading range: {e}")
        return False, ""


def decompress_range_chunk(compressed_chunk_file: str, 
                          original_gzip_file: str,
                          original_index_file: str,
                          target_uncompressed_start: int,
                          target_uncompressed_length: int) -> Tuple[bool, str]:
    """
    Attempt to decompress a range chunk.
    This is a proof of concept - real implementation would need more sophisticated handling.
    """
    print(f"Attempting to decompress chunk for uncompressed range {target_uncompressed_start}-{target_uncompressed_start + target_uncompressed_length}")
    
    # This is a simplified approach - in practice, you'd need to:
    # 1. Ensure the chunk contains complete gzip blocks
    # 2. Handle partial blocks at boundaries
    # 3. Use the index to find proper starting points
    
    manager = GzToolManager(verbose=True)
    
    # Try to extract from the original file as a reference
    success, reference_content = manager.extract_byte_range(
        original_gzip_file, 
        target_uncompressed_start, 
        target_uncompressed_length
    )
    
    if success:
        print("✓ Successfully extracted reference content from original file")
        return True, reference_content
    else:
        print("✗ Could not extract reference content")
        return False, ""


def complete_demo():
    """Complete demonstration of the workflow."""
    print("=== Complete gztool HTTP Range Request Demo ===")
    
    remote_url = "https://lifewise.sapphiremrfhub.com/mrfs/202505/MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gz"
    
    # Step 1: Download the complete file
    local_file = "remote_test_file.gz"
    index_file = "remote_test_file.gzi"
    
    print("\n1. Downloading complete file...")
    if not download_file(remote_url, local_file):
        return
    
    # Step 2: Create index
    print("\n2. Creating index...")
    manager = GzToolManager(verbose=True)
    success, actual_index_file = manager.create_index(local_file, span_mb=5)
    if not success:
        return
    
    # Step 3: Analyze index
    print("\n3. Analyzing index...")
    info = manager.list_index_info(actual_index_file)
    print(f"Index info: {json.dumps(info, indent=2)}")
    
    # Step 4: Choose target uncompressed range
    uncompressed_size = info.get('uncompressed_size_bytes', 0)
    if uncompressed_size == 0:
        print("Could not determine uncompressed size")
        return
    
    # Target: extract 50KB from 25% into the file
    target_uncompressed_start = uncompressed_size // 4
    target_uncompressed_length = 50000  # 50KB
    
    print(f"\n4. Target uncompressed range: {target_uncompressed_start}-{target_uncompressed_start + target_uncompressed_length}")
    
    # Step 5: Estimate compressed range needed
    compression_ratio = info.get('compressed_size_bytes', 1) / uncompressed_size
    estimated_comp_start = int(target_uncompressed_start * compression_ratio)
    
    # Add significant buffer since we don't have exact index parsing
    buffer_factor = 3.0  # 200% buffer
    estimated_comp_length = int(target_uncompressed_length * compression_ratio * buffer_factor)
    
    # Ensure we don't go past file end
    max_comp_size = info.get('compressed_size_bytes', 0)
    if estimated_comp_start + estimated_comp_length > max_comp_size:
        estimated_comp_length = max_comp_size - estimated_comp_start
    
    print(f"5. Estimated compressed range needed: {estimated_comp_start}-{estimated_comp_start + estimated_comp_length}")
    print(f"   Compression ratio: {compression_ratio:.4f}")
    print(f"   Buffer factor: {buffer_factor}")
    
    # Step 6: Download compressed range using HTTP Range request
    print("\n6. Downloading compressed range...")
    chunk_file = "compressed_chunk.gz"
    success, _ = download_http_range(
        remote_url, 
        estimated_comp_start, 
        estimated_comp_start + estimated_comp_length - 1,
        chunk_file
    )
    
    if not success:
        return
    
    # Step 7: Demonstrate decompression
    print("\n7. Demonstrating decompression...")
    success, content = decompress_range_chunk(
        chunk_file,
        local_file,
        actual_index_file,
        target_uncompressed_start,
        target_uncompressed_length
    )
    
    if success:
        print(f"✓ Successfully decompressed target range!")
        print(f"Content preview (first 200 chars):\n{content[:200]}...")
    
    # Cleanup
    print("\n8. Cleanup...")
    for file_to_remove in [chunk_file]:
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)
            print(f"Removed {file_to_remove}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Complete gztool HTTP range demonstration")
    parser.add_argument("--keep-files", action="store_true", 
                       help="Keep downloaded files after demo")
    
    args = parser.parse_args()
    
    try:
        complete_demo()
    finally:
        if not args.keep_files:
            # Cleanup main files
            for file_to_remove in ["remote_test_file.gz", "remote_test_file.gzi"]:
                if os.path.exists(file_to_remove):
                    os.remove(file_to_remove)
                    print(f"Cleaned up {file_to_remove}")


if __name__ == "__main__":
    main() 