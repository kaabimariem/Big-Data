#!/usr/bin/env python3
"""
Dashboard Big Data E-commerce - 1 000 000 lignes
Analyse complete avec segments clients, pays, remises, evolution temporelle
Usage: python scripts/dashboard.py
Ouvre: http://localhost:9090
"""

import csv
import json
import os
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'ecommerce_dataset_bigdata.csv')
PORT = 9090


def analyse_csv():
    global_revenue      = 0.0
    total_amount        = 0.0
    revenue_by_product  = defaultdict(float)
    sales_by_category   = defaultdict(int)
    top_products        = defaultdict(int)
    sales_by_date       = defaultdict(float)
    sales_by_month      = defaultdict(float)
    sales_by_country    = defaultdict(float)
    sales_by_city       = defaultdict(float)
    clients_by_segment  = defaultdict(set)
    revenue_by_segment  = defaultdict(float)
    discount_revenue    = defaultdict(float)
    transactions_count  = 0
    unique_clients      = set()

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                product   = row['product'].strip()
                category  = row['category'].strip()
                price     = float(row['price'])
                qty       = int(row['quantity'])
                client    = row['client_id'].strip()
                date      = row['date'][:10]
                month     = row['date'][:7]
                segment   = row.get('client_segment', 'standard').strip()
                discount  = float(row.get('discount_pct', 0))
                total     = float(row.get('total_amount', price * qty))
                country   = row.get('country', 'Unknown').strip()
                city      = row.get('city', 'Unknown').strip()

                rev = price * qty
                global_revenue            += rev
                total_amount              += total
                revenue_by_product[product] += rev
                sales_by_category[category] += qty
                top_products[product]       += qty
                sales_by_date[date]         += total
                sales_by_month[month]       += total
                sales_by_country[country]   += total
                sales_by_city[city]         += total
                clients_by_segment[segment].add(client)
                revenue_by_segment[segment] += total
                if discount > 0:
                    discount_revenue[str(int(discount))] += total
                unique_clients.add(client)
                transactions_count += 1
            except (ValueError, KeyError):
                continue

    return {
        "global_revenue":      round(global_revenue, 2),
        "total_amount":        round(total_amount, 2),
        "transactions_count":  transactions_count,
        "unique_clients":      len(unique_clients),
        "products_count":      len(revenue_by_product),
        "categories_count":    len(sales_by_category),
        "total_units":         sum(top_products.values()),
        "avg_basket":          round(total_amount / transactions_count, 2) if transactions_count else 0,

        # Sorted desc
        "revenue_by_product":  sorted(revenue_by_product.items(), key=lambda x: -x[1]),
        "sales_by_category":   sorted(sales_by_category.items(),  key=lambda x: -x[1]),
        "top_products":        sorted(top_products.items(),        key=lambda x: -x[1]),
        "sales_by_country":    sorted(sales_by_country.items(),   key=lambda x: -x[1]),
        "sales_by_city":       sorted(sales_by_city.items(),      key=lambda x: -x[1])[:10],
        "sales_by_month":      sorted(sales_by_month.items()),
        "clients_by_segment":  {k: len(v) for k, v in clients_by_segment.items()},
        "revenue_by_segment":  dict(sorted(revenue_by_segment.items(), key=lambda x: -x[1])),
        "discount_revenue":    dict(sorted(discount_revenue.items())),
    }


def build_html(d):
    jl = json.dumps

    rev_labels  = jl([k for k,v in d['revenue_by_product']])
    rev_values  = jl([round(v/1000,1) for k,v in d['revenue_by_product']])
    top_labels  = jl([k for k,v in d['top_products']])
    top_values  = jl([v for k,v in d['top_products']])
    cat_labels  = jl([k for k,v in d['sales_by_category']])
    cat_values  = jl([v for k,v in d['sales_by_category']])
    mon_labels  = jl([k for k,v in d['sales_by_month']])
    mon_values  = jl([round(v/1000,1) for k,v in d['sales_by_month']])
    ctr_labels  = jl([k for k,v in d['sales_by_country']])
    ctr_values  = jl([round(v/1000,1) for k,v in d['sales_by_country']])
    seg_labels  = jl(list(d['clients_by_segment'].keys()))
    seg_values  = jl(list(d['clients_by_segment'].values()))
    rseg_labels = jl(list(d['revenue_by_segment'].keys()))
    rseg_values = jl([round(v/1000,1) for v in d['revenue_by_segment'].values()])
    city_labels = jl([k for k,v in d['sales_by_city']])
    city_values = jl([round(v/1000,1) for k,v in d['sales_by_city']])

    rev_rows = "".join(
        f"<tr><td>{k}</td><td>{v/1000:,.1f}K &euro;</td><td>{v/d['global_revenue']*100:.1f}%</td></tr>"
        for k,v in d['revenue_by_product']
    )
    top_rows = "".join(
        f"<tr><td>{k}</td><td>{v:,}</td></tr>"
        for k,v in d['top_products']
    )
    cat_rows = "".join(
        f"<tr><td>{k}</td><td>{v:,}</td><td>{v/d['total_units']*100:.1f}%</td></tr>"
        for k,v in d['sales_by_category']
    )
    ctr_rows = "".join(
        f"<tr><td>{k}</td><td>{v/1000:,.1f}K &euro;</td></tr>"
        for k,v in d['sales_by_country']
    )
    seg_rows = "".join(
        f"<tr><td>{k}</td><td>{v:,}</td><td>{d['revenue_by_segment'].get(k,0)/1000:,.1f}K &euro;</td></tr>"
        for k,v in d['clients_by_segment'].items()
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
body{{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}}
header{{background:linear-gradient(135deg,#1e3a5f,#0284c7);padding:24px 32px}}
header h1{{font-size:1.6rem;font-weight:700}}
header p{{opacity:.75;margin-top:4px;font-size:.88rem}}
.badge{{background:rgba(255,255,255,.15);padding:3px 10px;border-radius:20px;font-size:.75rem;margin-left:8px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px;padding:20px 32px 0}}
.kpi{{background:#1e293b;border-radius:10px;padding:16px;border-left:4px solid #0ea5e9;transition:.2s}}
.kpi:hover{{transform:translateY(-2px);box-shadow:0 6px 20px #0002}}
.kpi .lbl{{font-size:.68rem;text-transform:uppercase;color:#94a3b8;letter-spacing:1px}}
.kpi .val{{font-size:1.55rem;font-weight:700;color:#38bdf8;margin-top:3px}}
.kpi .sub{{font-size:.68rem;color:#475569;margin-top:2px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:18px;padding:18px 32px}}
.card{{background:#1e293b;border-radius:12px;padding:20px}}
.card.wide{{grid-column:1/-1}}
.card.half{{min-width:200px}}
h2{{font-size:.8rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;display:flex;align-items:center;gap:6px}}
h2 i{{font-size:1rem}}
.cw{{position:relative;height:230px}}
.cw.tall{{height:290px}}
table{{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:12px}}
th{{background:#0f172a;color:#475569;text-align:left;padding:7px 12px;font-size:.68rem;text-transform:uppercase}}
td{{padding:7px 12px;border-bottom:1px solid #1e293b40}}
tr:hover td{{background:#0f172a60}}
td:last-child{{text-align:right;color:#64748b}}
footer{{text-align:center;padding:20px;color:#334155;font-size:.75rem;border-top:1px solid #1e293b;margin-top:8px}}
.btn{{position:fixed;bottom:20px;right:20px;background:#0ea5e9;color:#fff;border:none;
  padding:10px 18px;border-radius:8px;cursor:pointer;font-size:.85rem;box-shadow:0 4px 12px #0004}}
.btn:hover{{background:#0284c7}}
.tag{{background:#0ea5e920;color:#38bdf8;padding:2px 8px;border-radius:4px;font-size:.68rem}}
</style>
</head>
<body>

<header>
  <h1>&#128202; E-commerce Big Data Dashboard
    <span class="badge">&#9679; {d['transactions_count']:,} transactions</span>
    <span class="badge">{d['unique_clients']:,} clients</span>
  </h1>
  <p>Analyse Hadoop MapReduce &mdash; Dataset 1 000 000 lignes &mdash; 26 produits / 5 cat&eacute;gories / 7 pays</p>
</header>

<!-- KPI -->
<div class="kpi-grid">
  <div class="kpi"><div class="lbl">CA Brut</div>
    <div class="val">{d['global_revenue']/1e6:.2f}M&euro;</div><div class="sub">price &times; qty</div></div>
  <div class="kpi"><div class="lbl">CA Net</div>
    <div class="val">{d['total_amount']/1e6:.2f}M&euro;</div><div class="sub">apr&egrave;s remises</div></div>
  <div class="kpi"><div class="lbl">Transactions</div>
    <div class="val">{d['transactions_count']:,}</div><div class="sub">commandes</div></div>
  <div class="kpi"><div class="lbl">Clients</div>
    <div class="val">{d['unique_clients']:,}</div><div class="sub">IDs uniques</div></div>
  <div class="kpi"><div class="lbl">Unit&eacute;s</div>
    <div class="val">{d['total_units']:,}</div><div class="sub">articles vendus</div></div>
  <div class="kpi" style="border-color:#10b981"><div class="lbl">Panier moyen</div>
    <div class="val" style="color:#34d399">{d['avg_basket']:,.0f}&euro;</div><div class="sub">/ transaction</div></div>
  <div class="kpi" style="border-color:#f59e0b"><div class="lbl">Produits</div>
    <div class="val" style="color:#fbbf24">{d['products_count']}</div><div class="sub">{d['categories_count']} cat&eacute;gories</div></div>
  <div class="kpi" style="border-color:#8b5cf6"><div class="lbl">Remise moy.</div>
    <div class="val" style="color:#a78bfa">{round((1-d['total_amount']/d['global_revenue'])*100,1)}%</div>
    <div class="sub">sur CA brut</div></div>
</div>

<div class="grid">

  <!-- Evolution mensuelle -->
  <div class="card wide">
    <h2><i>&#128200;</i>&Eacute;volution du CA mensuel (en K&euro;)</h2>
    <div class="cw tall"><canvas id="lineChart"></canvas></div>
  </div>

  <!-- CA par produit -->
  <div class="card">
    <h2><i>&#128176;</i>CA par produit (K&euro;)</h2>
    <div class="cw"><canvas id="revChart"></canvas></div>
    <table><tr><th>Produit</th><th>CA</th><th>Part</th></tr>{rev_rows}</table>
  </div>

  <!-- Top produits quantite -->
  <div class="card">
    <h2><i>&#127942;</i>Top produits &mdash; quantit&eacute;s vendues</h2>
    <div class="cw"><canvas id="topChart"></canvas></div>
    <table><tr><th>Produit</th><th>Unit&eacute;s</th></tr>{top_rows}</table>
  </div>

  <!-- Ventes par categorie -->
  <div class="card">
    <h2><i>&#128230;</i>R&eacute;partition par cat&eacute;gorie</h2>
    <div class="cw"><canvas id="catChart"></canvas></div>
    <table><tr><th>Cat&eacute;gorie</th><th>Unit&eacute;s</th><th>Part</th></tr>{cat_rows}</table>
  </div>

  <!-- CA par pays -->
  <div class="card">
    <h2><i>&#127758;</i>CA par pays (K&euro;)</h2>
    <div class="cw"><canvas id="ctrChart"></canvas></div>
    <table><tr><th>Pays</th><th>CA Net</th></tr>{ctr_rows}</table>
  </div>

  <!-- Segments clients -->
  <div class="card">
    <h2><i>&#128100;</i>Segments clients</h2>
    <div class="cw"><canvas id="segChart"></canvas></div>
    <table><tr><th>Segment</th><th>Clients</th><th>CA Net</th></tr>{seg_rows}</table>
  </div>

  <!-- CA par segment -->
  <div class="card">
    <h2><i>&#128181;</i>CA net par segment (K&euro;)</h2>
    <div class="cw"><canvas id="rsegChart"></canvas></div>
  </div>

  <!-- Top villes -->
  <div class="card">
    <h2><i>&#127968;</i>Top 10 villes (K&euro;)</h2>
    <div class="cw"><canvas id="cityChart"></canvas></div>
  </div>

</div>

<footer>
  Hadoop MapReduce 3.3.6 &bull; Apache Spark &bull;
  1 000 000 transactions &bull; 100 000 clients &bull;
  <span class="tag">Big Data Project</span>
</footer>
<button class="btn" onclick="location.reload()">&#x1F504; Actualiser</button>

<script>
const C = ['#0ea5e9','#38bdf8','#7dd3fc','#22d3ee','#06b6d4',
           '#14b8a6','#10b981','#34d399','#a3e635','#facc15',
           '#f97316','#ef4444','#ec4899','#8b5cf6','#6366f1',
           '#f43f5e','#84cc16','#fb923c'];
const G  = '#1e293b';
const T  = '#94a3b8';
const ax = {{ ticks:{{color:T}}, grid:{{color:G}} }};
const noLeg = {{ legend:{{display:false}} }};

// Line - evolution mensuelle
new Chart('lineChart', {{
  type:'line',
  data:{{labels:{mon_labels},datasets:[{{
    label:'CA mensuel (K€)',data:{mon_values},
    borderColor:'#0ea5e9',backgroundColor:'rgba(14,165,233,.12)',
    fill:true,tension:.4,pointRadius:4,pointBackgroundColor:'#0ea5e9'
  }}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{labels:{{color:T}}}}}},
    scales:{{x:ax,y:{{...ax,ticks:{{...ax.ticks,callback:v=>v+'K'}}}}}}}}
}});

// Bar - CA produit
new Chart('revChart',{{
  type:'bar',
  data:{{labels:{rev_labels},datasets:[{{label:'CA (K€)',data:{rev_values},backgroundColor:C,borderRadius:5,borderSkipped:false}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:noLeg,
    scales:{{x:ax,y:{{...ax,ticks:{{...ax.ticks,callback:v=>v+'K'}}}}}}}}
}});

// Horizontal - top produits
new Chart('topChart',{{
  type:'bar',
  data:{{labels:{top_labels},datasets:[{{label:'Quantité',data:{top_values},backgroundColor:C,borderRadius:5}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:noLeg,scales:{{x:ax,y:ax}}}}
}});

// Doughnut - categorie
new Chart('catChart',{{
  type:'doughnut',
  data:{{labels:{cat_labels},datasets:[{{data:{cat_values},backgroundColor:C,borderColor:'#0f172a',borderWidth:3}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{color:T,padding:12}}}}}}}}
}});

// Bar - pays
new Chart('ctrChart',{{
  type:'bar',
  data:{{labels:{ctr_labels},datasets:[{{label:'CA (K€)',data:{ctr_values},backgroundColor:C,borderRadius:5,borderSkipped:false}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:noLeg,
    scales:{{x:ax,y:{{...ax,ticks:{{...ax.ticks,callback:v=>v+'K'}}}}}}}}
}});

// Pie - segments clients
new Chart('segChart',{{
  type:'pie',
  data:{{labels:{seg_labels},datasets:[{{data:{seg_values},backgroundColor:['#0ea5e9','#10b981','#f59e0b'],borderColor:'#0f172a',borderWidth:3}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{color:T}}}}}}}}
}});

// Bar - CA par segment
new Chart('rsegChart',{{
  type:'bar',
  data:{{labels:{rseg_labels},datasets:[{{label:'CA net (K€)',data:{rseg_values},backgroundColor:['#0ea5e9','#10b981','#f59e0b'],borderRadius:6,borderSkipped:false}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:noLeg,
    scales:{{x:ax,y:{{...ax,ticks:{{...ax.ticks,callback:v=>v+'K'}}}}}}}}
}});

// Bar horizontal - top villes
new Chart('cityChart',{{
  type:'bar',
  data:{{labels:{city_labels},datasets:[{{label:'CA (K€)',data:{city_values},backgroundColor:C,borderRadius:5}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:noLeg,
    scales:{{x:{{...ax,ticks:{{...ax.ticks,callback:v=>v+'K'}}}},y:ax}}}}
}});
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {self.command} {self.path}")

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
        except Exception:
            import traceback
            err = traceback.format_exc()
            print(f"[ERROR] {err}")
            body = f"<pre style='color:red;padding:20px'>{err}</pre>".encode()
            self.respond(500, "text/html", body)


if __name__ == "__main__":
    csv_abs = os.path.abspath(CSV_PATH)
    if not os.path.exists(csv_abs):
        print(f"[ERREUR] CSV introuvable: {csv_abs}")
        exit(1)

    print("Chargement du dataset (1M lignes - peut prendre ~10s)...")
    d = analyse_csv()
    print(f"[OK] {d['transactions_count']:,} transactions analysees")
    print(f"[OK] CA brut  : {d['global_revenue']/1e6:.2f} M EUR")
    print(f"[OK] CA net   : {d['total_amount']/1e6:.2f} M EUR")
    print(f"[OK] Clients  : {d['unique_clients']:,}")
    print(f"[OK] Segments : {list(d['clients_by_segment'].keys())}")
    print(f"[OK] Pays     : {[k for k,v in d['sales_by_country']]}")
    print(f"\nDashboard : http://localhost:{PORT}")
    print(f"API JSON  : http://localhost:{PORT}/api")
    print("Ctrl+C pour arreter\n")

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrete.")
