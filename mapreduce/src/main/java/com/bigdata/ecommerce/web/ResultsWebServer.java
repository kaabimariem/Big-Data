package com.bigdata.ecommerce.web;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;

import java.io.*;
import java.net.InetSocketAddress;
import java.util.*;

/**
 * Embedded HTTP server that reads MapReduce results from HDFS
 * and renders them as an interactive HTML dashboard.
 *
 * Usage: ResultsWebServer <hdfs-output-base> [port]
 * Example: ResultsWebServer /output/ecommerce 8090
 */
public class ResultsWebServer {

    private final String outputBase;
    private final int port;
    private final Configuration conf;

    public ResultsWebServer(String outputBase, int port) {
        this.outputBase = outputBase;
        this.port = port;
        this.conf = new Configuration();
    }

    // ── HDFS reader ──────────────────────────────────────────────────────────

    /** Read all lines from HDFS part files under a given directory. */
    private List<String> readHdfsLines(String path) {
        List<String> lines = new ArrayList<>();
        try {
            FileSystem fs = FileSystem.get(conf);
            Path dir = new Path(path);
            if (!fs.exists(dir)) return lines;

            org.apache.hadoop.fs.FileStatus[] statuses = fs.listStatus(dir);
            Arrays.sort(statuses, Comparator.comparing(s -> s.getPath().getName()));

            for (org.apache.hadoop.fs.FileStatus status : statuses) {
                String name = status.getPath().getName();
                if (!name.startsWith("part-")) continue;
                BufferedReader br = new BufferedReader(
                        new InputStreamReader(fs.open(status.getPath())));
                String line;
                while ((line = br.readLine()) != null) {
                    if (!line.trim().isEmpty()) lines.add(line.trim());
                }
                br.close();
            }
        } catch (Exception e) {
            lines.add("ERROR: " + e.getMessage());
        }
        return lines;
    }

    /** Parse tab-separated key→value lines into a LinkedHashMap. */
    private Map<String, Double> parseDoubleMap(List<String> lines) {
        Map<String, Double> map = new LinkedHashMap<>();
        for (String line : lines) {
            String[] parts = line.split("\t", 2);
            if (parts.length == 2) {
                try { map.put(parts[0].trim(), Double.parseDouble(parts[1].trim())); }
                catch (NumberFormatException ignored) {}
            }
        }
        return map;
    }

    private Map<String, Integer> parseIntMap(List<String> lines) {
        Map<String, Integer> map = new LinkedHashMap<>();
        for (String line : lines) {
            String[] parts = line.split("\t", 2);
            if (parts.length == 2) {
                try { map.put(parts[0].trim(), Integer.parseInt(parts[1].trim())); }
                catch (NumberFormatException ignored) {}
            }
        }
        return map;
    }

    // ── HTML builder ─────────────────────────────────────────────────────────

    private String buildDashboard() {
        List<String> globalLines   = readHdfsLines(outputBase + "/global-revenue");
        Map<String, Double>  revByProduct  = parseDoubleMap(readHdfsLines(outputBase + "/revenue-by-product"));
        Map<String, Integer> salesByCat    = parseIntMap(readHdfsLines(outputBase + "/sales-by-category"));
        Map<String, Integer> topProducts   = parseIntMap(readHdfsLines(outputBase + "/top-products"));

        double globalRevenue = 0;
        for (String line : globalLines) {
            String[] p = line.split("\t", 2);
            if (p.length == 2) try { globalRevenue = Double.parseDouble(p[1].trim()); } catch (Exception ignored) {}
        }

        // Sort by value descending
        List<Map.Entry<String, Double>> revList = new ArrayList<>(revByProduct.entrySet());
        revList.sort((a, b) -> Double.compare(b.getValue(), a.getValue()));

        List<Map.Entry<String, Integer>> topList = new ArrayList<>(topProducts.entrySet());
        topList.sort((a, b) -> Integer.compare(b.getValue(), a.getValue()));

        List<Map.Entry<String, Integer>> catList = new ArrayList<>(salesByCat.entrySet());
        catList.sort((a, b) -> Integer.compare(b.getValue(), a.getValue()));

        // ── JSON for charts ──
        String revLabels  = toJsonLabels(revList.stream().map(Map.Entry::getKey).collect(java.util.stream.Collectors.toList()));
        String revValues  = toJsonDoubles(revList.stream().map(Map.Entry::getValue).collect(java.util.stream.Collectors.toList()));
        String topLabels  = toJsonLabels(topList.stream().map(Map.Entry::getKey).collect(java.util.stream.Collectors.toList()));
        String topValues  = toJsonInts(topList.stream().map(Map.Entry::getValue).collect(java.util.stream.Collectors.toList()));
        String catLabels  = toJsonLabels(catList.stream().map(Map.Entry::getKey).collect(java.util.stream.Collectors.toList()));
        String catValues  = toJsonInts(catList.stream().map(Map.Entry::getValue).collect(java.util.stream.Collectors.toList()));

        // ── Table rows ──
        StringBuilder revRows = new StringBuilder();
        for (Map.Entry<String, Double> e : revList) {
            revRows.append("<tr><td>").append(esc(e.getKey())).append("</td><td>")
                   .append(String.format("%.2f", e.getValue())).append(" €</td></tr>");
        }

        StringBuilder topRows = new StringBuilder();
        for (Map.Entry<String, Integer> e : topList) {
            topRows.append("<tr><td>").append(esc(e.getKey())).append("</td><td>")
                   .append(e.getValue()).append(" unités</td></tr>");
        }

        StringBuilder catRows = new StringBuilder();
        for (Map.Entry<String, Integer> e : catList) {
            catRows.append("<tr><td>").append(esc(e.getKey())).append("</td><td>")
                   .append(e.getValue()).append("</td></tr>");
        }

        return "<!DOCTYPE html>\n" +
            "<html lang='fr'><head><meta charset='UTF-8'>" +
            "<meta name='viewport' content='width=device-width, initial-scale=1'>" +
            "<title>📊 Big Data E-commerce Dashboard</title>" +
            "<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'></script>" +
            "<style>" +
            "* { box-sizing: border-box; margin: 0; padding: 0; }" +
            "body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }" +
            "header { background: linear-gradient(135deg, #1e3a5f, #0ea5e9); padding: 24px 32px; }" +
            "header h1 { font-size: 1.8rem; font-weight: 700; }" +
            "header p  { opacity: .8; margin-top: 4px; font-size: .95rem; }" +
            ".kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; padding: 24px 32px 0; }" +
            ".kpi { background: #1e293b; border-radius: 12px; padding: 20px; border-left: 4px solid #0ea5e9; }" +
            ".kpi .label { font-size: .8rem; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; }" +
            ".kpi .value { font-size: 1.8rem; font-weight: 700; color: #38bdf8; margin-top: 6px; }" +
            ".grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 20px; padding: 24px 32px; }" +
            ".card { background: #1e293b; border-radius: 12px; padding: 20px; }" +
            ".card h2 { font-size: 1rem; color: #94a3b8; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px; }" +
            ".chart-wrap { position: relative; height: 260px; }" +
            "table { width: 100%; border-collapse: collapse; font-size: .9rem; margin-top: 12px; }" +
            "th { background: #0f172a; color: #64748b; text-align: left; padding: 8px 12px; font-size: .75rem; text-transform: uppercase; }" +
            "td { padding: 8px 12px; border-bottom: 1px solid #334155; }" +
            "tr:hover td { background: #0f172a; }" +
            "footer { text-align: center; padding: 20px; color: #475569; font-size: .8rem; }" +
            "</style></head><body>" +

            "<header><h1>📊 E-commerce Big Data Dashboard</h1>" +
            "<p>Résultats Hadoop MapReduce — Analyse des transactions e-commerce</p></header>" +

            // KPI cards
            "<div class='kpi-grid'>" +
            "<div class='kpi'><div class='label'>Chiffre d'affaires global</div>" +
            "<div class='value'>" + String.format("%.2f €", globalRevenue) + "</div></div>" +
            "<div class='kpi'><div class='label'>Produits analysés</div>" +
            "<div class='value'>" + revByProduct.size() + "</div></div>" +
            "<div class='kpi'><div class='label'>Catégories</div>" +
            "<div class='value'>" + salesByCat.size() + "</div></div>" +
            "<div class='kpi'><div class='label'>Total ventes (unités)</div>" +
            "<div class='value'>" + topProducts.values().stream().mapToInt(Integer::intValue).sum() + "</div></div>" +
            "</div>" +

            // Charts + tables
            "<div class='grid'>" +

            // Revenue by product — bar chart
            "<div class='card'><h2>💰 Chiffre d'affaires par produit</h2>" +
            "<div class='chart-wrap'><canvas id='revChart'></canvas></div>" +
            "<table><tr><th>Produit</th><th>CA</th></tr>" + revRows + "</table></div>" +

            // Top products — horizontal bar
            "<div class='card'><h2>🏆 Top produits (quantités vendues)</h2>" +
            "<div class='chart-wrap'><canvas id='topChart'></canvas></div>" +
            "<table><tr><th>Produit</th><th>Qté</th></tr>" + topRows + "</table></div>" +

            // Sales by category — doughnut
            "<div class='card'><h2>📦 Ventes par catégorie</h2>" +
            "<div class='chart-wrap'><canvas id='catChart'></canvas></div>" +
            "<table><tr><th>Catégorie</th><th>Unités</th></tr>" + catRows + "</table></div>" +

            "</div>" +

            "<footer>Hadoop MapReduce 3.3.6 · Dataset: ecommerce_dataset_bigdata.csv · " +
            "Généré le " + new Date() + "</footer>" +

            // Chart.js scripts
            "<script>" +
            "const COLORS=['#0ea5e9','#38bdf8','#7dd3fc','#22d3ee','#06b6d4','#14b8a6','#10b981','#34d399','#a3e635','#facc15'];" +

            // Revenue bar chart
            "new Chart(document.getElementById('revChart'),{type:'bar',data:{" +
            "labels:" + revLabels + ",datasets:[{label:'CA (€)'," +
            "data:" + revValues + ",backgroundColor:COLORS,borderRadius:6,borderSkipped:false}]}," +
            "options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}," +
            "scales:{x:{ticks:{color:'#94a3b8'},grid:{color:'#1e293b'}}," +
            "y:{ticks:{color:'#94a3b8'},grid:{color:'#334155'}}}}});" +

            // Top products horizontal bar
            "new Chart(document.getElementById('topChart'),{type:'bar',data:{" +
            "labels:" + topLabels + ",datasets:[{label:'Quantité'," +
            "data:" + topValues + ",backgroundColor:COLORS,borderRadius:6}]}," +
            "options:{indexAxis:'y',responsive:true,maintainAspectRatio:false," +
            "plugins:{legend:{display:false}}," +
            "scales:{x:{ticks:{color:'#94a3b8'},grid:{color:'#334155'}}," +
            "y:{ticks:{color:'#94a3b8'},grid:{color:'#1e293b'}}}}});" +

            // Category doughnut
            "new Chart(document.getElementById('catChart'),{type:'doughnut',data:{" +
            "labels:" + catLabels + ",datasets:[{data:" + catValues + "," +
            "backgroundColor:COLORS,borderColor:'#0f172a',borderWidth:2}]}," +
            "options:{responsive:true,maintainAspectRatio:false," +
            "plugins:{legend:{position:'right',labels:{color:'#94a3b8'}}}}});" +
            "</script></body></html>";
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private String esc(String s) { return s.replace("&","&amp;").replace("<","&lt;"); }
    private String toJsonLabels(List<String> l) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < l.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append("\"").append(l.get(i).replace("\"","\\\"")).append("\"");
        }
        return sb.append("]").toString();
    }
    private String toJsonDoubles(List<Double> l) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < l.size(); i++) { if (i > 0) sb.append(","); sb.append(String.format("%.2f", l.get(i))); }
        return sb.append("]").toString();
    }
    private String toJsonInts(List<Integer> l) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < l.size(); i++) { if (i > 0) sb.append(","); sb.append(l.get(i)); }
        return sb.append("]").toString();
    }

    // ── HTTP handler ──────────────────────────────────────────────────────────

    public void start() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        server.createContext("/", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                String html = buildDashboard();
                byte[] bytes = html.getBytes("UTF-8");
                exchange.getResponseHeaders().add("Content-Type", "text/html; charset=UTF-8");
                exchange.sendResponseHeaders(200, bytes.length);
                OutputStream os = exchange.getResponseBody();
                os.write(bytes);
                os.close();
            }
        });

        // JSON API endpoint for raw data
        server.createContext("/api/results", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                Map<String, Double> rev = parseDoubleMap(readHdfsLines(outputBase + "/revenue-by-product"));
                Map<String, Integer> top = parseIntMap(readHdfsLines(outputBase + "/top-products"));
                Map<String, Integer> cat = parseIntMap(readHdfsLines(outputBase + "/sales-by-category"));
                List<String> global = readHdfsLines(outputBase + "/global-revenue");

                StringBuilder json = new StringBuilder("{");
                json.append("\"global_revenue\":");
                double g = 0;
                for (String l : global) { String[] p = l.split("\t",2); if (p.length==2) try { g=Double.parseDouble(p[1].trim()); } catch(Exception e){} }
                json.append(String.format("%.2f", g)).append(",");

                json.append("\"revenue_by_product\":{");
                boolean first = true;
                for (Map.Entry<String,Double> e : rev.entrySet()) {
                    if (!first) json.append(","); first=false;
                    json.append("\"").append(e.getKey().replace("\"","\\\"")).append("\":").append(String.format("%.2f",e.getValue()));
                }
                json.append("},\"top_products\":{"); first=true;
                for (Map.Entry<String,Integer> e : top.entrySet()) {
                    if (!first) json.append(","); first=false;
                    json.append("\"").append(e.getKey().replace("\"","\\\"")).append("\":").append(e.getValue());
                }
                json.append("},\"sales_by_category\":{"); first=true;
                for (Map.Entry<String,Integer> e : cat.entrySet()) {
                    if (!first) json.append(","); first=false;
                    json.append("\"").append(e.getKey().replace("\"","\\\"")).append("\":").append(e.getValue());
                }
                json.append("}}");

                byte[] bytes = json.toString().getBytes("UTF-8");
                exchange.getResponseHeaders().add("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, bytes.length);
                OutputStream os = exchange.getResponseBody();
                os.write(bytes);
                os.close();
            }
        });

        server.setExecutor(null);
        server.start();
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║  Dashboard: http://localhost:" + port + "          ║");
        System.out.println("║  API JSON:  http://localhost:" + port + "/api/results ║");
        System.out.println("╚══════════════════════════════════════════╝");
    }

    // ── Main ──────────────────────────────────────────────────────────────────

    public static void main(String[] args) throws Exception {
        String outputBase = args.length > 0 ? args[0] : "/output/ecommerce";
        int port = args.length > 1 ? Integer.parseInt(args[1]) : 8090;

        System.out.println("Reading HDFS results from: " + outputBase);
        ResultsWebServer server = new ResultsWebServer(outputBase, port);
        server.start();

        // Keep running
        Thread.currentThread().join();
    }
}
