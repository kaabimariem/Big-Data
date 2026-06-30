#!/usr/bin/env python3
"""
Dashboard web e-commerce - lit les resultats MapReduce depuis HDFS
Lance: python scripts/web_dashboard.py
Ouvre: http://localhost:8090
"""

import subprocess
import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

HDFS_OUTPUT = "/output/ecommerce"
PORT = 8090


def hdfs_cat(hdfs_path):
    """Lit un fichier HDFS via docker exec hadoop-master."""
    try:
        result = subprocess.run(
            ["docker", "exec", "hadoop-master",
             "hdfs", "dfs", "-cat", hdfs_path],
            capture_output=True, text=True, timeout=20
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"[WARN] hdfs_cat({hdfs_path}): {e}")
        return ""


def read_hdfs_results():
    data = {
        "global_revenue": 0.0,
        "revenue_by_product": {},
        "sales_by_category": {},
        "top_products": {}
    }

    # Global revenue
    for line in hdfs_cat(f"{HDFS_OUTPUT}/global-revenue/part-r-00000").splitlines():
        p = line.split("\t")
        if len(p) == 2:
            try: data["global_revenue"] = float(p[1])
            except: pass

    # Revenue by product
    for line in hdfs_cat(f"{HDFS_OUTPUT}/revenue-by-product/part-r-00000").splitlines():
        p = line.split("\t")
        if len(p) == 2:
            try: data["revenue_by_product"][p[0].strip()] = float(p[1])
            except: pass

    # Sales by category
    for line in hdfs_cat(f"{HDFS_OUTPUT}/sales-by-category/part-r-00000").splitlines():
        p = line.split("\t")
        if len(p) == 2:
            try: data["sales_by_category"][p[0].strip()] = int(p[1])
            except: pass

    # Top products
    for line in hdfs_cat(f"{HDFS_OUTPUT}/top-products/part-r-00000").splitlines():
        p = line.split("\t")
        if len(p) == 2:
            try: data["top_products"][p[0].strip()] = int(p[1])
            except: pass

    return data


def build_html(data):
    rev  = sorted(data["revenue_by_product"].items(), key=lambda x: -x[1])
    top  = sorted(data["top_products"].items(),       key=lambda x: -x[1])
    cat  = sorted(data["sales_by_category"].items(),  key=lambda x: -x[1])
    total_units = sum(data["top_products"].values())

    def jl(lst): return json.dumps(lst)

    rev_rows = "".join(f"<tr><td>{k}</td><td>{v:,.2f} &euro;</td></tr>" for k,v in rev)
    top_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in top)
    cat_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in cat)

    # fallback si pas encore de donnees
    if not rev:
        rev_rows = "<tr><td colspan='2' style='color:#64748b'>Pas encore de donnees</td></tr>"
    if not top:
        top_rows = "<tr><td colspan='2' style='color:#64748b'>Pas encore de donnees</td></tr>"
    if not cat:
        cat_rows = "<tr><td colspan='2' style='color:#64748b'>Pas encore de donnees</td></tr>"

    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Big Data E-commerce Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
    header{background:linear-gradient(135deg,#1e3a5f,#0ea5e9);padding:24px 32px}
    header h1{font-size:1.8rem;font-weight:700}
    header p{opacity:.8;margin-top:4px}
    .kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;padding:24px 32px 0}
    .kpi{background:#1e293b;border-radius:12px;padding:20px;border-left:4px solid #0ea5e9}
    .kpi .label{font-size:.8rem;text-transform:uppercase;color:#94a3b8;letter-spacing:1px}
    .kpi .value{font-size:1.8rem;font-weight:700;color:#38bdf8;margin-top:6px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:20px;padding:24px 32px}
    .card{background:#1e293b;border-radius:12px;padding:20px}
    .card h2{font-size:.95rem;color:#94a3b8;margin-bottom:16px;text-transform:uppercase;letter-spacing:1px}
    .chart-wrap{position:relative;height:240px}
    table{width:100%;border-collapse:collapse;font-size:.88rem;margin-top:12px}
    th{background:#0f172a;color:#64748b;text-align:left;padding:8px 12px;font-size:.75rem;text-transform:uppercase}
    td{padding:8px 12px;border-bottom:1px solid #334155}
    tr:hover td{background:#0f172a}
    footer{text-align:center;padding:20px;color:#475569;font-size:.8rem}
    .btn-refresh{position:fixed;bottom:24px;right:24px;background:#0ea5e9;color:#fff;
      border:none;padding:12px 20px;border-radius:8px;cursor:pointer;font-size:.9rem;box-shadow:0 4px 12px rgba(0,0,0,.4)}
    .btn-refresh:hover{background:#0284c7}
  </style>
</head>
<body>
<header>
  <h1>&#128202; E-commerce Big Data Dashboard</h1>
  <p>Resultats Hadoop MapReduce &mdash; Analyse des transactions e-commerce</p>
</header>

<div class="kpi-grid">
  <div class="kpi">
    <div class="label">Chiffre d&apos;affaires global</div>
    <div class="value">""" + f"{data['global_revenue']:,.2f} &euro;" + """</div>
  </div>
  <div class="kpi">
    <div class="label">Produits analys&eacute;s</div>
    <div class="value">""" + str(len(data['revenue_by_product'])) + """</div>
  </div>
  <div class="kpi">
    <div class="label">Cat&eacute;gories</div>
    <div class="value">""" + str(len(data['sales_by_category'])) + """</div>
  </div>
  <div class="kpi">
    <div class="label">Total ventes (unit&eacute;s)</div>
    <div class="value">""" + str(total_units) + """</div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>&#128176; Chiffre d&apos;affaires par produit</h2>
    <div class="chart-wrap"><canvas id="revChart"></canvas></div>
    <table><tr><th>Produit</th><th>CA</th></tr>""" + rev_rows + """</table>
  </div>
  <div class="card">
    <h2>&#127942; Top produits (quantit&eacute;s vendues)</h2>
    <div class="chart-wrap"><canvas id="topChart"></canvas></div>
    <table><tr><th>Produit</th><th>Qt&eacute;</th></tr>""" + top_rows + """</table>
  </div>
  <div class="card">
    <h2>&#128230; Ventes par cat&eacute;gorie</h2>
    <div class="chart-wrap"><canvas id="catChart"></canvas></div>
    <table><tr><th>Cat&eacute;gorie</th><th>Unit&eacute;s</th></tr>""" + cat_rows + """</table>
  </div>
</div>

<footer>Hadoop MapReduce 3.3.6 &bull; Dataset: ecommerce_dataset_bigdata.csv</footer>
<button class="btn-refresh" onclick="location.reload()">&#x1F504; Actualiser</button>

<script>
const C=['#0ea5e9','#38bdf8','#7dd3fc','#22d3ee','#06b6d4','#14b8a6','#10b981','#34d399','#a3e635','#facc15'];
""" + f"""
new Chart(document.getElementById('revChart'),{{
  type:'bar',
  data:{{labels:{jl([k for k,v in rev])},datasets:[{{label:'CA',data:{jl([round(v,2) for k,v in rev])},backgroundColor:C,borderRadius:6,borderSkipped:false}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#94a3b8'}},grid:{{color:'#1e293b'}}}},y:{{ticks:{{color:'#94a3b8'}},grid:{{color:'#334155'}}}}}}}}
}});

new Chart(document.getElementById('topChart'),{{
  type:'bar',
  data:{{labels:{jl([k for k,v in top])},datasets:[{{label:'Qte',data:{jl([v for k,v in top])},backgroundColor:C,borderRadius:6}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#94a3b8'}},grid:{{color:'#334155'}}}},y:{{ticks:{{color:'#94a3b8'}},grid:{{color:'#1e293b'}}}}}}}}
}});

new Chart(document.getElementById('catChart'),{{
  type:'doughnut',
  data:{{labels:{jl([k for k,v in cat])},datasets:[{{data:{jl([v for k,v in cat])},backgroundColor:C,borderColor:'#0f172a',borderWidth:2}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{color:'#94a3b8'}}}}}}}}
}});
""" + """
</script>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {fmt % args}")

    def send_html(self, body: str):
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, obj: dict):
        payload = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        try:
            if self.path == "/api/results":
                self.send_json(read_hdfs_results())
            else:
                data = read_hdfs_results()
                self.send_html(build_html(data))
        except Exception:
            err = traceback.format_exc()
            print(f"[ERROR] {err}")
            msg = f"<pre style='color:red'>{err}</pre>"
            payload = msg.encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)


if __name__ == "__main__":
    print(f"Reading results from HDFS: {HDFS_OUTPUT}")
    print(f"Dashboard: http://localhost:{PORT}")
    print(f"API JSON:  http://localhost:{PORT}/api/results")
    print("Ctrl+C to stop\n")

    # Test rapide de connexion Docker
    test = subprocess.run(
        ["docker", "exec", "hadoop-master", "echo", "OK"],
        capture_output=True, text=True, timeout=5
    )
    if test.stdout.strip() == "OK":
        print("[OK] Docker container hadoop-master accessible")
    else:
        print("[WARN] Cannot reach hadoop-master — check: docker ps")

    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
