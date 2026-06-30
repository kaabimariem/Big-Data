package com.bigdata.ecommerce.category;

import com.bigdata.ecommerce.CsvParser;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

public class SalesByCategoryMapper extends Mapper<Object, Text, Text, IntWritable> {

    private final Text categoryKey = new Text();
    private final IntWritable quantity = new IntWritable();

    @Override
    protected void map(Object key, Text value, Context context)
            throws IOException, InterruptedException {

        CsvParser.Transaction tx = CsvParser.parse(value.toString());
        if (tx == null) {
            return;
        }

        categoryKey.set(tx.category);
        quantity.set(tx.quantity);
        context.write(categoryKey, quantity);
    }
}
