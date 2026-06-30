"""
Spark Streaming - Real-time e-commerce analysis
Monitors a directory for new CSV lines and computes:
  - Real-time sales by product (windowed aggregation)
  - Top products in sliding window
  - Anomaly detection (sales spike alert)
"""
import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, count, window, from_csv
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType


SCHEMA = StructType([
    StructField("transaction_id", StringType()),
    StructField("date", StringType()),
    StructField("product", StringType()),
    StructField("category", StringType()),
    StructField("price", DoubleType()),
    StructField("quantity", IntegerType()),
    StructField("client_id", StringType()),
])

ALERT_THRESHOLD = 100
WINDOW_DURATION = "1 minute"
SLIDE_DURATION = "30 seconds"


def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    batch_df = batch_df.withColumn("revenue", col("price") * col("quantity"))

    print(f"\n--- Batch {batch_id} ---")

    print("Ventes par produit (batch courant):")
    batch_df.groupBy("product") \
        .agg(spark_sum("quantity").alias("qty"), spark_sum("revenue").alias("revenue")) \
        .orderBy(col("qty").desc()) \
        .show(truncate=False)

    total_qty = batch_df.agg(spark_sum("quantity")).collect()[0][0] or 0
    if total_qty > ALERT_THRESHOLD:
        print(f"ALERTE: pic de ventes detecte ({total_qty} unites en ce batch)")


def main():
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "stream_input"
    checkpoint = sys.argv[2] if len(sys.argv) > 2 else "stream_checkpoint"

    os.makedirs(input_dir, exist_ok=True)

    spark = SparkSession.builder \
        .appName("EcommerceStreaming") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    raw_stream = spark.readStream \
        .schema(SCHEMA) \
        .option("header", True) \
        .option("maxFilesPerTrigger", 1) \
        .csv(input_dir)

    raw_stream = raw_stream.withColumn("revenue", col("price") * col("quantity"))

    print("=== Top produits en temps reel (fenetre glissante) ===")
    windowed = raw_stream \
        .withWatermark("date", "2 minutes") \
        .groupBy(window(col("date"), WINDOW_DURATION, SLIDE_DURATION), col("product")) \
        .agg(spark_sum("quantity").alias("total_qty"), spark_sum("revenue").alias("total_revenue"))

    query_top = windowed \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", False) \
        .start()

    query_batch = raw_stream \
        .writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", checkpoint) \
        .start()

    print(f"Streaming actif. Deposez des fichiers CSV dans: {input_dir}")
    print(f"Seuil d'alerte: {ALERT_THRESHOLD} ventes par batch")

    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
