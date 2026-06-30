#!/bin/bash
# Sort top products MapReduce output (run after batch job)

HDFS_OUTPUT="${1:-/output/ecommerce/top-products}"
LOCAL="/tmp/top-products-sorted.txt"

hdfs dfs -cat "$HDFS_OUTPUT/part-r-*" | sort -t$'\t' -k2 -nr > "$LOCAL"

echo "=== Top Products (sorted by quantity) ==="
head -20 "$LOCAL"
