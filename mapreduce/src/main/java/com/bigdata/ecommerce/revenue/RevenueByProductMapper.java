package com.bigdata.ecommerce.revenue;

import com.bigdata.ecommerce.CsvParser;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

public class RevenueByProductMapper extends Mapper<Object, Text, Text, DoubleWritable> {

    private final Text productKey = new Text();
    private final DoubleWritable revenue = new DoubleWritable();

    @Override
    protected void map(Object key, Text value, Context context)
            throws IOException, InterruptedException {

        CsvParser.Transaction tx = CsvParser.parse(value.toString());
        if (tx == null) {
            return;
        }

        productKey.set(tx.product);
        revenue.set(tx.revenue());
        context.write(productKey, revenue);
    }
}
