#!/bin/bash
# research_refresh.sh - Complete Research Data Pipeline
# 
# This script demonstrates the complete workflow for generating
# publication-ready research materials from gztool performance data.
#
# Usage: ./research_refresh.sh [num_tests]
# Example: ./research_refresh.sh 30

set -e  # Exit on any error

# Configuration
NUM_TESTS=${1:-30}
EXTRACT_LENGTH=1000
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# File paths
CSV_OUTPUT="research_results_${TIMESTAMP}.csv"
GRAPH_DIR="research_graphs_${TIMESTAMP}"
REPORT_OUTPUT="research_analysis_${TIMESTAMP}.md"
TABLE_OUTPUT="research_table_${TIMESTAMP}.md"

echo "🔬 Research Data Pipeline - gztool Performance Analysis"
echo "========================================================"
echo "📅 Timestamp: $(date)"
echo "🧪 Test Configuration:"
echo "   - Number of tests: ${NUM_TESTS}"
echo "   - Extract length: ${EXTRACT_LENGTH} bytes"
echo "   - Output directory: ${GRAPH_DIR}"
echo ""

# Step 1: Generate fresh performance data
echo "📊 Step 1: Running performance tests..."
echo "Command: python test-gztool.py --num-tests ${NUM_TESTS} --csv-output ${CSV_OUTPUT} --graph-output ${GRAPH_DIR} --extract-length ${EXTRACT_LENGTH}"

python test-gztool.py --num-tests ${NUM_TESTS} \
                      --csv-output ${CSV_OUTPUT} \
                      --graph-output ${GRAPH_DIR} \
                      --extract-length ${EXTRACT_LENGTH}

echo "✅ Performance tests completed"
echo ""

# Step 2: Generate supplementary visualizations
echo "📈 Step 2: Creating supplementary visualizations..."

python csv_to_formats.py ${CSV_OUTPUT} \
                         --summary-viz ${GRAPH_DIR}/comprehensive_summary.png \
                         --table-image ${GRAPH_DIR}/publication_table.png \
                         --markdown-report ${REPORT_OUTPUT}

echo "✅ Supplementary visualizations created"
echo ""

# Step 3: Generate markdown tables for embedding
echo "📋 Step 3: Creating embeddable markdown tables..."

python csv_to_formats.py ${CSV_OUTPUT} \
                         --markdown-table ${TABLE_OUTPUT} \
                         --max-rows 15

echo "✅ Markdown tables generated"
echo ""

# Step 4: Display summary statistics
echo "📊 Step 4: Performance Summary"
echo "=============================="

python csv_to_formats.py ${CSV_OUTPUT}

echo ""

# Step 5: Generate file inventory
echo "📁 Step 5: Generated Files Inventory"
echo "===================================="

echo "📈 Graph Files (${GRAPH_DIR}):"
ls -la ${GRAPH_DIR}/ | grep -E '\.(png|jpg|jpeg)$' | awk '{print "   📊 " $9 " (" $5 " bytes)"}'

echo ""
echo "📄 Data Files:"
echo "   📋 ${CSV_OUTPUT} ($(wc -l < ${CSV_OUTPUT}) rows of experimental data)"
echo "   📊 ${REPORT_OUTPUT} (detailed analysis report)"
echo "   📝 ${TABLE_OUTPUT} (embeddable markdown table)"

echo ""
echo "🔍 Quick Data Preview:"
echo "======================"
echo "First 5 rows of experimental data:"
head -6 ${CSV_OUTPUT} | column -t -s','

echo ""
echo "📊 Test Results Summary:"
echo "======================="

# Extract key metrics using CSV analysis
python3 << EOF
import pandas as pd
import sys

try:
    df = pd.read_csv('${CSV_OUTPUT}')
    
    print(f"🧪 Total Tests: {len(df)}")
    print(f"✅ Success Rate: {df['success'].mean() * 100:.1f}%")
    print(f"⚡ Mean Speedup: {df['speedup'].mean():.1f}x (Range: {df['speedup'].min():.1f}x - {df['speedup'].max():.1f}x)")
    print(f"⏱️  Mean Access Time: {df['gztool_time'].mean() * 1000:.1f}ms (Range: {df['gztool_time'].min() * 1000:.1f}ms - {df['gztool_time'].max() * 1000:.1f}ms)")
    print(f"📏 File Coverage: {df['position_gb'].min():.2f}GB - {df['position_gb'].max():.2f}GB")
    
    # Top 3 performers
    top_3 = df.nlargest(3, 'speedup')[['test_id', 'index_point', 'speedup', 'gztool_time']]
    print(f"\n🏆 Top 3 Performance Results:")
    for _, row in top_3.iterrows():
        print(f"   #{int(row['test_id'])}: Index {int(row['index_point'])} - {row['speedup']:.1f}x speedup ({row['gztool_time']*1000:.1f}ms)")
        
except Exception as e:
    print(f"❌ Error analyzing data: {e}")
    sys.exit(1)
EOF

echo ""
echo "🔄 Refresh Commands for Future Updates:"
echo "======================================="
echo "# Regenerate with same parameters:"
echo "./research_refresh.sh ${NUM_TESTS}"
echo ""
echo "# Regenerate with different test count:"
echo "./research_refresh.sh 50"
echo ""
echo "# Manual regeneration steps:"
echo "python test-gztool.py --num-tests ${NUM_TESTS} --csv-output new_results.csv --graph-output new_graphs"
echo "python csv_to_formats.py new_results.csv --summary-viz new_graphs/summary.png"
echo ""

# Step 6: Create archive link
echo "📦 Step 6: Creating research archive link..."

# Create a symlink to the latest results for easy access
ln -sf ${CSV_OUTPUT} latest_research_results.csv
ln -sf ${GRAPH_DIR} latest_research_graphs
ln -sf ${REPORT_OUTPUT} latest_research_analysis.md

echo "✅ Archive links created:"
echo "   📊 latest_research_results.csv -> ${CSV_OUTPUT}"
echo "   📈 latest_research_graphs/ -> ${GRAPH_DIR}/"
echo "   📄 latest_research_analysis.md -> ${REPORT_OUTPUT}"

echo ""
echo "🎉 Research Pipeline Complete!"
echo "=============================="
echo "All research materials have been generated and are ready for publication."
echo ""
echo "📋 Next Steps:"
echo "1. Review generated graphs in ${GRAPH_DIR}/"
echo "2. Include data table from ${TABLE_OUTPUT} in your paper"
echo "3. Reference visualizations from the graphs directory"
echo "4. Use ${REPORT_OUTPUT} for detailed analysis"
echo ""
echo "🔗 For integration into research papers:"
echo "![Performance Overview](${GRAPH_DIR}/performance_overview.png)"
echo "![Comprehensive Summary](${GRAPH_DIR}/comprehensive_summary.png)"
echo ""
echo "Timestamp: $(date)" 