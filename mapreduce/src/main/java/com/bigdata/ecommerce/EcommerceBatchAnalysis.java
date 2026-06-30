package com.bigdata.ecommerce;

import com.bigdata.ecommerce.category.SalesByCategory;
import com.bigdata.ecommerce.global.GlobalRevenueJob;
import com.bigdata.ecommerce.revenue.RevenueByProduct;
import com.bigdata.ecommerce.topproducts.TopProducts;
import com.bigdata.ecommerce.web.ResultsWebServer;

/**
 * Runs all e-commerce batch MapReduce jobs sequentially,
 * then starts an embedded HTTP dashboard to display results.
 *
 * Usage: EcommerceBatchAnalysis <hdfs-input> <hdfs-output-base> [web-port]
 * Example: EcommerceBatchAnalysis /input/ecommerce /output/ecommerce 8090
 */
public class EcommerceBatchAnalysis {

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: EcommerceBatchAnalysis <hdfs-input> <hdfs-output-base> [web-port]");
            System.err.println("Example: EcommerceBatchAnalysis /input/ecommerce /output/ecommerce 8090");
            System.exit(1);
        }

        String input      = args[0];
        String outputBase = args[1];
        int    webPort    = args.length > 2 ? Integer.parseInt(args[2]) : 8090;

        // ── Run MapReduce jobs ───────────────────────────────────────────────
        System.out.println("=== 1/4 Global Revenue ===");
        if (!GlobalRevenueJob.run(input, outputBase + "/global-revenue")) {
            System.err.println("GlobalRevenue job failed."); System.exit(1);
        }

        System.out.println("=== 2/4 Revenue by Product ===");
        if (!RevenueByProduct.run(input, outputBase + "/revenue-by-product")) {
            System.err.println("RevenueByProduct job failed."); System.exit(1);
        }

        System.out.println("=== 3/4 Sales by Category ===");
        if (!SalesByCategory.run(input, outputBase + "/sales-by-category")) {
            System.err.println("SalesByCategory job failed."); System.exit(1);
        }

        System.out.println("=== 4/4 Top Products ===");
        if (!TopProducts.run(input, outputBase + "/top-products")) {
            System.err.println("TopProducts job failed."); System.exit(1);
        }

        System.out.println("\nAll batch jobs completed successfully!");

        // ── Start web dashboard ──────────────────────────────────────────────
        System.out.println("\nStarting web dashboard...");
        ResultsWebServer webServer = new ResultsWebServer(outputBase, webPort);
        webServer.start();

        // Keep the JVM alive so the web server stays up
        Thread.currentThread().join();
    }
}
