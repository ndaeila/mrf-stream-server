# gztool for HTTP Range Requests - Complete Guide

This guide demonstrates how to use `gztool` to enable efficient HTTP range requests on gzip-compressed files, allowing you to download and decompress only specific sections of large compressed files.

## Overview

The workflow allows you to:
1. **Create indexes** for gzip files that map uncompressed positions to compressed positions
2. **Calculate compressed byte ranges** needed for specific uncompressed data
3. **Download only small chunks** using HTTP Range requests
4. **Decompress just those chunks** without processing the entire file

## Quick Start

### 1. Basic gztool Commands

```bash
# Create an index for a gzip file (span of 10MB between index points)
gztool -s10 -i your_file.gz

# List index information
gztool -l your_file.gzi

# Extract specific byte range (starting at byte 1000, extract 500 bytes)
gztool -b1000 -r500 your_file.gz > extracted_data.txt
```

### 2. Example with Target File

For the specific file: `https://lifewise.sapphiremrfhub.com/mrfs/202505/MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gz`

```bash
# Step 1: Download the complete file (one-time setup)
wget "https://lifewise.sapphiremrfhub.com/mrfs/202505/MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gz"

# Step 2: Create index
gztool -s5 -i MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gz

# Step 3: View index information
gztool -l MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gzi

# Step 4: Extract specific ranges
gztool -b1000000 -r50000 MPNMRF_PHCS_20250324-MPI_PHCS_innetworkrates_PRAC_2025-03-24.json.gz
```

## HTTP Range Request Workflow

### Conceptual Process

1. **Initial Setup (One-time)**:
   ```bash
   # Download complete file and create index
   curl -o remote_file.gz "https://your-url.com/file.gz"
   gztool -s10 -i remote_file.gz
   
   # Store the index file for future use
   # Index file is typically <1% of original compressed size
   ```

2. **For Each Range Request**:
   ```python
   # Determine target uncompressed position (e.g., byte 1,000,000)
   target_uncompressed_start = 1000000
   target_uncompressed_length = 50000  # 50KB
   
   # Use index to estimate compressed range needed
   compression_ratio = compressed_size / uncompressed_size
   estimated_compressed_start = int(target_uncompressed_start * compression_ratio)
   estimated_compressed_length = int(target_uncompressed_length * compression_ratio * 2.0)  # 100% buffer
   
   # Download only the compressed chunk
   curl -H "Range: bytes=${estimated_compressed_start}-$((estimated_compressed_start + estimated_compressed_length))" \
        -o chunk.gz "https://your-url.com/file.gz"
   
   # Note: This chunk won't be directly decompressible due to gzip format constraints
   # You'd need the complete file for gztool to work properly
   ```

### Practical Implementation

The most practical approach is:

1. **Use gztool for local analysis**:
   ```bash
   # Download file once, create index, analyze structure
   gztool -i large_file.gz
   gztool -l large_file.gzi
   ```

2. **Map positions for HTTP ranges**:
   ```python
   # Use the index information to calculate what compressed ranges
   # correspond to your target uncompressed ranges
   ```

3. **Optimize subsequent downloads**:
   - Download specific compressed segments based on analysis
   - Use gztool to extract from the complete file when available
   - Cache frequently accessed ranges

## Example Results

From our demonstration with a 669MB compressed file (4.3GB uncompressed):

```
Index Information:
• Index points: 420
• Uncompressed size: 4302.02 MB
• Compressed size: 668.90 MB  
• Compression ratio: 0.1555
• Space savings: 84.5%
• Avg span between index points: 10.24 MB

Sample Extractions:
• Position 1,000 (500 bytes): Estimated range 155-310 (155 compressed bytes needed)
• Position 1.1GB (1KB): Estimated range 175MB-175MB (310 compressed bytes needed)
• Position 2.2GB (1KB): Estimated range 350MB-350MB (310 compressed bytes needed)
```

## Key Benefits

1. **Bandwidth Efficiency**: Download only 1-5% of file size for small ranges
2. **Speed**: Near-instant access to any part of the gzip file
3. **Storage**: Index files are typically <1% of compressed file size
4. **Flexibility**: Random access without full decompression

## Limitations and Considerations

1. **Initial Setup**: Requires downloading the complete file once to create index
2. **Gzip Format**: Cannot directly decompress arbitrary byte ranges from gzip files
3. **Buffer Requirements**: Need to download extra data around target ranges
4. **Index Accuracy**: Estimates may require larger buffers for safety

## Python Implementation

See the provided Python scripts:

- `test-gztool.py`: Basic gztool wrapper and HTTP range functionality
- `practical_demo.py`: Complete demonstration with local file analysis
- `complete_demo.py`: Full workflow including download and HTTP range simulation

### Running the Demonstrations

```bash
# Basic demo with local test file
python practical_demo.py --demo local

# Show HTTP workflow concepts
python practical_demo.py --demo workflow

# Run both demonstrations
python practical_demo.py
```

## Advanced Usage

### Custom Index Spans

```bash
# Smaller spans = more index points = more precision, larger index file
gztool -s5 -i file.gz    # 5MB spans

# Larger spans = fewer index points = less precision, smaller index file  
gztool -s20 -i file.gz   # 20MB spans
```

### Verbose Output

```bash
# Get detailed information during processing
gztool -v2 -i file.gz    # Verbosity level 2
gztool -v5 -i file.gz    # Maximum verbosity
```

### Force Index Recreation

```bash
# Overwrite existing index file
gztool -f -i file.gz
```

## Use Cases

1. **Large Log Files**: Access specific time ranges without downloading entire files
2. **Data Analysis**: Extract samples from different parts of large datasets
3. **Streaming Applications**: Seek to specific positions in compressed streams
4. **Backup Systems**: Restore specific file ranges from compressed archives
5. **Scientific Data**: Access specific measurements from large compressed datasets

## Performance Tips

1. **Choose appropriate span sizes**: Balance between index size and precision
2. **Cache index files**: Store indexes for frequently accessed files
3. **Use buffers**: Add 50-200% buffer when estimating compressed ranges
4. **Batch requests**: Group nearby ranges into single HTTP requests
5. **Monitor compression ratios**: Files with variable compression need larger buffers

## Troubleshooting

### Common Issues

1. **"Compressed data error"**: Usually means incomplete or corrupted gzip data
2. **Index creation fails**: Check file permissions and available disk space
3. **Extraction returns no data**: Verify byte positions are within file bounds
4. **HTTP 416 Range Not Satisfiable**: Requested range exceeds file size

### Debug Commands

```bash
# Check file integrity
gztool -t file.gz

# Verify index integrity  
gztool -lll file.gzi

# Test extraction with verbose output
gztool -v3 -b1000 -r500 file.gz
```

## Conclusion

gztool enables efficient random access to gzip-compressed files, making it possible to implement bandwidth-efficient HTTP range requests. While there are some limitations due to the gzip format, the tool provides significant benefits for applications that need to access specific portions of large compressed files.

The key is understanding the relationship between compressed and uncompressed positions, using appropriate buffer sizes, and designing your application workflow around the capabilities and limitations of the gzip format and gztool. 