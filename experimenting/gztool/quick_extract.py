#!/usr/bin/env python3
import subprocess
import sys

# Calculate position for index point 311 out of 420 total points
# 4,510,998,952 total uncompressed bytes from our previous analysis
total_uncompressed = 4510998952
total_index_points = 420
target_index_point = 311

# Calculate approximate byte position for index point 311
position = int((target_index_point / total_index_points) * total_uncompressed)
extract_length = 2000  # Extract 2KB of data

print(f"Extracting from index point {target_index_point}/420")
print(f"Estimated position: {position:,} bytes")
print(f"Extracting {extract_length} bytes...")

# Run gztool to extract the data
cmd = ["gztool", f"-b{position}", f"-r{extract_length}", "data/test-file.gz"]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print(f"\n=== REAL DECOMPRESSED DATA FROM POSITION {position:,} ===")
    print(result.stdout)
    print("=" * 60)
    print(f"✅ Successfully extracted {len(result.stdout)} characters of real data")
else:
    print(f"❌ Error: {result.stderr}")
    sys.exit(1) 