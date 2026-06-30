#!/usr/bin/env python3
"""
Dashboard Big Data E-commerce
Analyse complete du dataset CSV + interface web interactive
Usage: python scripts/dashboard.py
Ouvre: http://localhost:8090
"""

import csv
import json
import os
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'ecommerce_dataset_bigdata.csv')
PORT = 9090


def analyse_csv():
    """Simule les jobs MapReduce : lit le CSV et calcule toutes les stats."""
    global_revenue = 0.0
    revenue_by_product = defaultdict(float)
    sales_by_category  = defaultdict(int)
    top_products       = defaultdict(int)
    sales_by_date      = defaultdict(float)
    transactions_count = 0
    unique_clients     = set()

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                product  = row['product'].strip()
                category = row['category'].strip()
                price    = float(row['price'])
                qty      = int(row['quantity'])
                client   = row['client_id'].strip()
                date     = row['date'][:10]          # YYYY-MM-DD

                rev = price * qty
                global_revenue             += rev
                revenue_by_product[product]+= rev
                sales_by_category[category]+= qty
                top_products[product]      += qty
                sales_by_date[date]        += rev
                unique_clients.add(client)
                transactions_count         += 1
            except (ValueError, KeyError):
                continue

    # Trier
    rev_sorted = sorted(revenue_by_product.items(), key=lambda x: -x[1])
    top_sorted = sorted(top_products.items(),        key=lambda x: -x[1])
    cat_sorted = sorted(sales_by_category.items(),   key=lambda x: -x[1])
    date_sorted= sorted(sales_by_date.items())

    return {
        "global_revenue":      round(global_revenue, 2),
        "transactions_count":  transactions_count,
        "unique_clients":      len(unique_clients),
        "products_count":      len(revenue_by_product),
        "categories_count":    len(sales_by_category),
        "total_units":         sum(top_products.values()),
        "revenue_by_product":  rev_sorted,
        "sales_by_category":   cat_sorted,
        "top_products":        top_sorted,
        "sales_by_date":       date_sorted,
    }


def build_html(d):
    jl = json.dumps

    rev_labels = jl([k for k,v in d['revenue_by_product']])
    rev_values = jl([round(v,2) for k,v in d['revenue_by_product']])
    top_labels = jl([k for k,v in d['top_products']])
    top_values = jl([v for k,v in d['top_products']])
    cat_labels = jl([k for k,v in d['sales_by_category']])
    cat_values = jl([v for k,v in d['sales_by_category']])
    date_labels= jl([k for k,v in d['sales_by_date']])
    date_values= jl([round(v,2) for k,v in d['sales_by_date']])

    rev_rows = "".join(
        f"<tr><td>{k}</td><td>{v:,.2f} &euro;</td>"
        f"<td>{round(v/d['global_revenue']*100,1)}%</td></tr>"
        for k,v in d['revenue_by_product']
    )
    top_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k,v in d['top_products']
    )
    cat_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td>"
        f"<td>{round(v/d['total_units']*100,1)}%</td></tr>"
        for k,v in d['sales_by_category']
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Big Data E-commerce Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0}}
header{{background:linear-gradient(135deg,#1e3a5f 0%,#0ea5e9 100%);padding:28px 32px;display:flex;align-items:center;gap:16px}}
header h1{{font-size:1.7rem;font-weight:700}}
header p{{opacity:.75;margin-top:4px;font-size:.9rem}}
.badge{{background:rgba(255,255,255,.15);padding:4px 12px;border-radius:20px;font-size:.8rem}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;padding:24px 32px 0}}
.kpi{{background:#1e293b;border-radius:10px;padding:18px;border-left:4px solid #0ea5e9;transition:.2s}}
.kpi:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.3)}}
.kpi .label{{font-size:.72rem;text-transform:uppercase;color:#94a3b8;letter-spacing:1px}}
.kpi .value{{font-size:1.7rem;font-weight:700;color:#38bdf8;margin-top:4px}}
.kpi .sub{{font-size:.72rem;color:#64748b;margin-top:2px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:20px;padding:20px 32px}}
.card{{background:#1e293b;border-radius:12px;padding:22px}}
.card.wide{{grid-column:1/-1}}
.card h2{{font-size:.88rem;color:#64748b;margin-bottom:14px;text-transform:uppercase;letter-spacing:1px;display:flex;align-items:center;gap:8px}}
.card h2 span{{font-size:1.1rem}}
.chart-wrap{{position:relative;height:250px}}
.chart-wrap.tall{{height:300px}}
table{{width:100%;border-collapse:collapse;font-size:.85rem;margin-top:14px}}
th{{background:#0f172a;color:#475569;text-align:left;padding:8px 14px;font-size:.72rem;text-transform:uppercase;letter-spacing:.5px}}
td{{padding:8px 14px;border-bottom:1px solid #1e293b}}
tr:hover td{{background:#0f172a40}}
td:last-child{{text-align:right;color:#64748b}}
footer{{text-align:center;padding:24px;color:#334155;font-size:.8rem;border-top:1px solid #1e293b;margin-top:8px}}
.tag{{display:inline-block;background:#0ea5e920;color:#38bdf8;padding:2px 8px;border-radius:4px;font-size:.7rem}}
</style>
</head>
<body>

<header>
  <div>
    <h1>&#128202; E-commerce Big Data Dashboard</h1>
    <p>Analyse Hadoop MapReduce &mdash; Dataset e-commerce &nbsp;
      <span class="badge">&#x2022; {d['transactions_count']} transactions</span>
    </p>
  </div>
</header>

<!-- KPI cards -->
<div class="kpi-grid">
  <div class="kpi">
    <div class="label">CA Global</div>
    <div class="value">{d['global_revenue']:,.0f} &euro;</div>
    <div class="sub">Chiffre d&apos;affaires total</div>
  </div>
  <div class="kpi">
    <div class="label">Transactions</div>
    <div class="value">{d['transactions_count']}</div>
    <div class="sub">Ventes enregistr&eacute;es</div>
  </div>
  <div class="kpi">
    <div class="label">Clients uniques</div>
    <div class="value">{d['unique_clients']}</div>
    <div class="sub">IDs distincts</div>
  </div>
  <div class="kpi">
    <div class="label">Produits</div>
    <div class="value">{d['products_count']}</div>
    <div class="sub">{d['categories_count']} cat&eacute;gories</div>
  </div>
  <div class="kpi">
    <div class="label">Unit&eacute;s vendues</div>
    <div class="value">{d['total_units']}</div>
    <div class="sub">Quantit&eacute; totale</div>
  </div>
  <div class="kpi" style="border-left-color:#10b981">
    <div class="label">Panier moyen</div>
    <div class="value" style="color:#34d399">{d['global_revenue']/d['transactions_count']:,.0f} &euro;</div>
    <div class="sub">Par transaction</div>
  </div>
</div>

<!-- Charts -->
<div class="grid">

  <!-- Evolution CA par jour -->
  <div class="card wide">
    <h2><span>&#128200;</span> &Eacute;volution du CA quotidien</h2>
    <div class="chart-wrap tall"><canvas id="lineChart"></canvas></div>
  </div>

  <!-- CA par produit -->
  <div class="card">
    <h2><span>&#128176;</span> Chiffre d&apos;affaires par produit</h2>
    <div class="chart-wrap"><canvas id="revChart"></canvas></div>
    <table>
      <tr><th>Produit</th><th>CA</th><th>Part</th></tr>
      {rev_rows}
    </table>
  </div>

  <!-- Top produits -->
  <div class="card">
    <h2><span>&#127942;</span> Top produits &mdash; quantit&eacute;s vendues</h2>
    <div class="chart-wrap"><canvas id="topChart"></canvas></div>
    <table>
      <tr><th>Produit</th><th>Qte</th></tr>
      {top_rows}
    </table>
  </div>

  <!-- Ventes par catégorie -->
  <div class="card">
    <h2><span>&#128230;</span> Ventes par cat&eacute;gorie</h2>
    <div class="chart-wrap"><canvas id="catChart"></canvas></div>
    <table>
      <tr><th>Cat&eacute;gorie</th><th>Unit&eacute;s</th><th>Part</th></tr>
      {cat_rows}
    </table>
  </div>

</div>

<footer>
  Hadoop MapReduce 3.3.6 &bull; Apache Spark &bull;
  Dataset: ecommerce_dataset_bigdata.csv &bull;
  <span class="tag">Big Data Project</span>
</footer>

<script>
const C = ['#0ea5e9','#38bdf8','#7dd3fc','#22d3ee','#06b6d4',
           '#14b8a6','#10b981','#34d399','#a3e635','#facc15',
           '#f97316','#ef4444','#ec4899','#8b5cf6','#6366f1'];

const gridColor  = '#1e293b';
const tickColor  = '#94a3b8';
const axisStyle  = {{ ticks:{{color:tickColor}}, grid:{{color:gridColor}} }};

// Line chart - evolution CA
new Chart(document.getElementById('lineChart'), {{
  type: 'line',
  data: {{
    labels: {date_labels},
    datasets: [{{
      label: 'CA (\u20ac)',
      data: {date_values},
      borderColor: '#0ea5e9',
      backgroundColor: 'rgba(14,165,233,.15)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointBackgroundColor: '#0ea5e9'
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: tickColor }} }} }},
    scales: {{ x: axisStyle, y: axisStyle }}
  }}
}});

// Bar chart - CA par produit
new Chart(document.getElementById('revChart'), {{
  type: 'bar',
  data: {{
    labels: {rev_labels},
    datasets: [{{ label:'CA (\u20ac)', data:{rev_values},
      backgroundColor: C, borderRadius: 6, borderSkipped: false }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: axisStyle, y: axisStyle }}
  }}
}});

// Horizontal bar - top produits
new Chart(document.getElementById('topChart'), {{
  type: 'bar',
  data: {{
    labels: {top_labels},
    datasets: [{{ label:'Quantit\u00e9', data:{top_values},
      backgroundColor: C, borderRadius: 6 }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: axisStyle, y: axisStyle }}
  }}
}});

// Doughnut - categories
new Chart(document.getElementById('catChart'), {{
  type: 'doughnut',
  data: {{
    labels: {cat_labels},
    datasets: [{{ data:{cat_values},
      backgroundColor: C, borderColor: '#0f172a', borderWidth: 3 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position:'right', labels:{{ color: tickColor, padding:16 }} }} }}
  }}
}});
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} [{self.command}] {self.path}")

    def respond(self, code, ctype, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            data = analyse_csv()
            if self.path == "/api":
                payload = json.dumps(data, default=list, indent=2).encode()
                self.respond(200, "application/json; charset=utf-8", payload)
            else:
                html = build_html(data).encode("utf-8")
                self.respond(200, "text/html; charset=utf-8", html)
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            print(f"[ERROR] {err}")
            body = f"<pre>{err}</pre>".encode()
            self.respond(500, "text/html", body)


if __name__ == "__main__":
    csv_abs = os.path.abspath(CSV_PATH)
    if not os.path.exists(csv_abs):
        print(f"[ERREUR] CSV introuvable: {csv_abs}")
        exit(1)

    # Test analyse
    d = analyse_csv()
    print(f"[OK] CSV lu: {d['transactions_count']} transactions")
    print(f"[OK] CA global: {d['global_revenue']:,.2f} EUR")
    print(f"[OK] Produits: {list(d['revenue_by_product'])[:3]} ...")
    print(f"\nDashboard: http://localhost:{PORT}")
    print(f"API JSON:  http://localhost:{PORT}/api")
    print("Ctrl+C pour arreter\n")

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrete.")
