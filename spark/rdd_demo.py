"""
Demonstration RDD Spark - transformations et actions
A executer dans spark-shell ou avec spark-submit
"""
from pyspark.sql import SparkSession


def main():
    spark = SparkSession.builder.appName("RDD-Demo").getOrCreate()
    sc = spark.sparkContext

    print("\n=== 1. Creation RDD depuis fichier ===")
    rdd1 = sc.textFile("ecommerce_dataset_bigdata.csv")
    print(f"Nombre de lignes: {rdd1.count()}")

    print("\n=== 2. Transformation flatMap (split) ===")
    rdd2 = rdd1.flatMap(lambda line: line.split(","))
    print(f"Nombre d'elements apres split: {rdd2.count()}")

    print("\n=== 3. Transformation filter (Electronics) ===")
    header = rdd1.first()
    data_rdd = rdd1.filter(lambda line: line != header)
    electronics = data_rdd.filter(lambda line: "Electronics" in line)
    print(f"Transactions Electronics: {electronics.count()}")

    print("\n=== 4. Transformation map (product, revenue) ===")
    def parse_revenue(line):
        parts = line.split(",")
        if len(parts) < 6:
            return ("UNKNOWN", 0.0)
        product = parts[2]
        try:
            revenue = float(parts[4]) * int(parts[5])
        except ValueError:
            revenue = 0.0
        return (product, revenue)

    revenue_rdd = data_rdd.map(parse_revenue)

    print("\n=== 5. Action reduceByKey (CA par produit) ===")
    revenue_by_product = revenue_rdd.reduceByKey(lambda a, b: a + b)
    top5 = revenue_by_product.takeOrdered(5, key=lambda x: -x[1])
    for product, rev in top5:
        print(f"  {product:15s} {rev:>12,.2f} EUR")

    print("\n=== 6. Action collect (echantillon) ===")
    sample = rdd2.take(10)
    print(f"Echantillon: {sample[:5]}...")

    spark.stop()


if __name__ == "__main__":
    main()
