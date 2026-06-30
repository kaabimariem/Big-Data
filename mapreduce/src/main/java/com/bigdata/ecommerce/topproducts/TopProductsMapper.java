package com.bigdata.ecommerce.topproducts;

import com.bigdata.ecommerce.CsvParser;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

public class TopProductsMapper extends Mapper<Object, Text, Text, IntWritable> {

    private final Text productKey = new Text();
    private static final IntWritable ONE = new IntWritable(1);

    @Override
    protected void map(Object key, Text value, Context context)
            throws IOException, InterruptedException {

        CsvParser.Transaction tx = CsvParser.parse(value.toString());
        if (tx == null) {
            return;
        }

        productKey.set(tx.product);
        context.write(productKey, new IntWritable(tx.quantity));
    }
}
