"""
Spark Batch Analysis - E-commerce transactions
Calculates global revenue, revenue by product, sales by category, and top products.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, count, desc


def main():
    spark = SparkSession.builder \
        .appName("EcommerceBatchAnalysis") \
        .getOrCreate()

    input_path = "ecommerce_dataset_bigdata.csv"
    df = spark.read.option("header", True).option("inferSchema", True).csv(input_path)

    df = df.withColumn("revenue", col("price") * col("quantity"))

    print("\n=== Chiffre d'affaires global ===")
    global_revenue = df.agg(spark_sum("revenue").alias("total_revenue"))
    global_revenue.show()

    print("\n=== Chiffre d'affaires par produit ===")
    revenue_by_product = df.groupBy("product") \
        .agg(spark_sum("revenue").alias("revenue")) \
        .orderBy(desc("revenue"))
    revenue_by_product.show()

    print("\n=== Ventes par catégorie ===")
    sales_by_category = df.groupBy("category") \
        .agg(spark_sum("quantity").alias("total_quantity")) \
        .orderBy(desc("total_quantity"))
    sales_by_category.show()

    print("\n=== Top produits (quantité vendue) ===")
    top_products = df.groupBy("product") \
        .agg(spark_sum("quantity").alias("total_sold"), count("*").alias("transactions")) \
        .orderBy(desc("total_sold"))
    top_products.show()

    spark.stop()


if __name__ == "__main__":
    main()
