package com.bigdata.ecommerce.category;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class SalesByCategory {

    public static boolean run(String input, String output) throws Exception {
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "sales by category");

        job.setJarByClass(SalesByCategory.class);
        job.setMapperClass(SalesByCategoryMapper.class);
        job.setCombinerClass(SalesByCategoryReducer.class);
        job.setReducerClass(SalesByCategoryReducer.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);

        FileInputFormat.addInputPath(job, new Path(input));
        FileOutputFormat.setOutputPath(job, new Path(output));

        return job.waitForCompletion(true);
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("Usage: SalesByCategory <input> <output>");
            System.exit(1);
        }
        System.exit(run(args[0], args[1]) ? 0 : 1);
    }
}
