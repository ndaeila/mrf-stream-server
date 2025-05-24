# Detailed Research Data Analysis Report

**Generated from:** research_results.csv
**Total Records:** 30
**Analysis Date:** 2025-05-23 18:42:47

## Executive Summary

- **Mean Performance Improvement:** 1587.9x faster than linear access
- **Median Performance Improvement:** 1890.3x faster than linear access
- **Performance Range:** 163.5x to 3417.0x improvement
- **Average Access Time:** 7.4 milliseconds
- **Access Time Consistency:** ±2.0ms standard deviation
- **Reliability:** 100.0% success rate

## Complete Dataset

### Performance Metrics Table

| Test Id | Index Point | Position Gb | Gztool Time | Estimated Linear Time | Speedup | Success |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 123 | 1.23 | 0.0049s | 6.30s | 1298.1x | True |
| 2 | 42 | 0.42 | 0.0091s | 2.15s | 237.4x | True |
| 3 | 412 | 4.12 | 0.0096s | 21.10s | 2200.5x | True |
| 4 | 400 | 4.00 | 0.0109s | 20.49s | 1885.0x | True |
| 5 | 200 | 2.00 | 0.0051s | 10.24s | 1989.6x | True |
| 6 | 264 | 2.64 | 0.0054s | 13.52s | 2487.3x | True |
| 7 | 52 | 0.52 | 0.0095s | 2.66s | 279.6x | True |
| 8 | 34 | 0.34 | 0.0107s | 1.74s | 163.5x | True |
| 9 | 251 | 2.51 | 0.0066s | 12.85s | 1948.6x | True |
| 10 | 335 | 3.35 | 0.0050s | 17.16s | 3417.0x | True |
| 11 | 81 | 0.81 | 0.0072s | 4.15s | 577.0x | True |
| 12 | 269 | 2.69 | 0.0062s | 13.78s | 2210.2x | True |
| 13 | 133 | 1.33 | 0.0095s | 6.81s | 719.1x | True |
| 14 | 400 | 4.00 | 0.0090s | 20.49s | 2288.4x | True |
| 15 | 200 | 2.00 | 0.0034s | 10.24s | 2995.9x | True |
| 16 | 215 | 2.15 | 0.0051s | 11.01s | 2145.5x | True |
| 17 | 306 | 3.06 | 0.0065s | 15.67s | 2410.3x | True |
| 18 | 70 | 0.70 | 0.0065s | 3.59s | 548.7x | True |
| 19 | 158 | 1.58 | 0.0093s | 8.09s | 872.4x | True |
| 20 | 305 | 3.05 | 0.0070s | 15.62s | 2229.5x | True |
| 21 | 69 | 0.69 | 0.0069s | 3.53s | 514.2x | True |
| 22 | 318 | 3.18 | 0.0059s | 16.29s | 2750.5x | True |
| 23 | 353 | 3.53 | 0.0095s | 18.08s | 1895.6x | True |
| 24 | 365 | 3.65 | 0.0100s | 18.69s | 1874.6x | True |
| 25 | 164 | 1.64 | 0.0084s | 8.40s | 994.6x | True |
| 26 | 363 | 3.63 | 0.0088s | 18.59s | 2119.1x | True |
| 27 | 88 | 0.88 | 0.0064s | 4.51s | 700.4x | True |
| 28 | 248 | 2.48 | 0.0060s | 12.70s | 2103.1x | True |
| 29 | 158 | 1.58 | 0.0090s | 8.09s | 896.5x | True |
| 30 | 95 | 0.95 | 0.0055s | 4.87s | 885.7x | True |

## Statistical Analysis

### Speedup Performance

| Statistic | Value |
|-----------|-------|
| Count | 30 |
| Mean | 1587.9x |
| Standard Deviation | 900.7x |
| Minimum | 163.5x |
| 25th Percentile | 757.4x |
| Median | 1890.3x |
| 75th Percentile | 2207.8x |
| Maximum | 3417.0x |

### Access Time Performance

| Metric | Value |
|--------|-------|
| Mean Access Time | 7.43ms |
| Standard Deviation | 2.02ms |
| Minimum Access Time | 3.40ms |
| Maximum Access Time | 10.90ms |

## Data Refresh Commands

To regenerate this analysis with updated data:

```bash
# Update graphs and data
python test-gztool.py --num-tests 30 --csv-output research_results.csv --graph-output research_graphs

# Regenerate this report
python csv_to_formats.py research_results.csv --markdown-report updated_report.md

# Create new table images
python csv_to_formats.py research_results.csv --table-image updated_table.png
```

---
*Report generated automatically from research data*