/**
 * Spark Streaming - E-commerce (Scala)
 * Equivalent Scala version for spark-shell / spark-submit
 */
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

object EcommerceStreaming {

  def main(args: Array[String]): Unit = {
    val inputDir = if (args.length > 0) args(0) else "stream_input"

    val spark = SparkSession.builder()
      .appName("EcommerceStreamingScala")
      .getOrCreate()

    import spark.implicits._

    spark.sparkContext.setLogLevel("WARN")

    val stream = spark.readStream
      .option("header", value = true)
      .schema("transaction_id STRING, date STRING, product STRING, category STRING, price DOUBLE, quantity INT, client_id STRING")
      .csv(inputDir)
      .withColumn("revenue", $"price" * $"quantity")

    // Top products en direct
    val topProducts = stream
      .groupBy($"product")
      .agg(sum("quantity").as("total_qty"), sum("revenue").as("total_revenue"))

    val query = topProducts.writeStream
      .outputMode("complete")
      .format("console")
      .option("truncate", false)
      .start()

    // Detection d'anomalies
    stream.writeStream
      .foreachBatch { (batchDF: org.apache.spark.sql.DataFrame, batchId: Long) =>
        val count = batchDF.agg(sum("quantity")).collect()(0).getLong(0)
        if (count > 100) {
          println(s"ALERTE: pic de ventes ($count unites) - batch $batchId")
        }
      }
      .start()

    query.awaitTermination()
  }
}
