#!/bin/bash
# Upload dataset to HDFS and run MapReduce jobs inside hadoop-master container

set -e

DATASET="${1:-/data/ecommerce_dataset_bigdata.csv}"
HDFS_INPUT="/input/ecommerce"
HDFS_OUTPUT="/output/ecommerce"
JAR="/apps/ecommerce-mapreduce.jar"

echo "=== Upload dataset to HDFS ==="
hdfs dfs -mkdir -p /input
hdfs dfs -put -f "$DATASET" "$HDFS_INPUT"
hdfs dfs -ls "$HDFS_INPUT"

echo "=== Clean previous output ==="
hdfs dfs -rm -r -f "$HDFS_OUTPUT" || true

echo "=== Run batch MapReduce jobs ==="
hadoop jar "$JAR" com.bigdata.ecommerce.EcommerceBatchAnalysis "$HDFS_INPUT" "$HDFS_OUTPUT"

echo "=== Results ==="
echo "--- Global Revenue ---"
hdfs dfs -cat "$HDFS_OUTPUT/global-revenue/part-r-00000"

echo "--- Revenue by Product ---"
hdfs dfs -cat "$HDFS_OUTPUT/revenue-by-product/part-r-*"

echo "--- Sales by Category ---"
hdfs dfs -cat "$HDFS_OUTPUT/sales-by-category/part-r-*"

echo "--- Top Products ---"
hdfs dfs -cat "$HDFS_OUTPUT/top-products/part-r-*"
