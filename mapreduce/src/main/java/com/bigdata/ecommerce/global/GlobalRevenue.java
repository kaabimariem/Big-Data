package com.bigdata.ecommerce.global;

import com.bigdata.ecommerce.CsvParser;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;

/**
 * Computes global revenue (single reducer key).
 */
public class GlobalRevenue {

    public static class MapperClass extends Mapper<Object, Text, Text, DoubleWritable> {

        private static final Text GLOBAL_KEY = new Text("TOTAL_REVENUE");
        private final DoubleWritable revenue = new DoubleWritable();

        @Override
        protected void map(Object key, Text value, Context context)
                throws IOException, InterruptedException {

            CsvParser.Transaction tx = CsvParser.parse(value.toString());
            if (tx == null) {
                return;
            }

            revenue.set(tx.revenue());
            context.write(GLOBAL_KEY, revenue);
        }
    }

    public static class ReducerClass extends Reducer<Text, DoubleWritable, Text, DoubleWritable> {

        private final DoubleWritable result = new DoubleWritable();

        @Override
        protected void reduce(Text key, Iterable<DoubleWritable> values, Context context)
                throws IOException, InterruptedException {

            double sum = 0.0;
            for (DoubleWritable val : values) {
                sum += val.get();
            }
            result.set(sum);
            context.write(key, result);
        }
    }
}
