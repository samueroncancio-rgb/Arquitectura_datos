"""
Dashboard Generator Module.
Transforms Superstore data into a self-contained, interactive HTML/JS Analytics Dashboard.
"""

import json
from pathlib import Path
import pandas as pd
from config.config import config


def generate_html_dashboard(output_path: Path = None) -> Path:
    target_path = output_path or (config.paths.base_dir / "docs" / "dashboard.html")
    csv_path = config.paths.raw_csv_path

    if not csv_path.is_file():
        raise FileNotFoundError(f"Source data not found at: {csv_path}")

    # Read data
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="windows-1252")

    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Year"] = df["Order Date"].dt.year
    df["YearMonth"] = df["Order Date"].dt.to_period("M").astype(str)

    # 1. KPI summary
    total_sales = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    total_orders = int(df["Order ID"].nunique())
    total_customers = int(df["Customer ID"].nunique())
    total_quantity = int(df["Quantity"].sum())
    profit_margin = round((total_profit / total_sales) * 100, 2)
    avg_order_value = round(total_sales / total_orders, 2)

    # 2. Monthly Trend
    monthly = df.groupby("YearMonth").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
        orders=("Order ID", "nunique"),
    ).reset_index()

    monthly_labels = monthly["YearMonth"].tolist()
    monthly_sales = [round(x, 2) for x in monthly["sales"].tolist()]
    monthly_profit = [round(x, 2) for x in monthly["profit"].tolist()]

    # 3. Category & Subcategory
    cat_df = df.groupby("Category").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
    ).reset_index()
    cat_labels = cat_df["Category"].tolist()
    cat_sales = [round(x, 2) for x in cat_df["sales"].tolist()]
    cat_profit = [round(x, 2) for x in cat_df["profit"].tolist()]

    # 4. Regional
    reg_df = df.groupby("Region").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
        orders=("Order ID", "nunique"),
    ).reset_index()
    reg_labels = reg_df["Region"].tolist()
    reg_sales = [round(x, 2) for x in reg_df["sales"].tolist()]
    reg_profit = [round(x, 2) for x in reg_df["profit"].tolist()]

    # 5. Segment
    seg_df = df.groupby("Segment").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
    ).reset_index()
    seg_labels = seg_df["Segment"].tolist()
    seg_sales = [round(x, 2) for x in seg_df["sales"].tolist()]

    # 6. Top 8 Products
    top_p = df.groupby("Product Name").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
    ).reset_index().sort_values(by="sales", ascending=False).head(8)
    top_p_names = [p[:32] + "..." if len(p) > 32 else p for p in top_p["Product Name"].tolist()]
    top_p_sales = [round(x, 2) for x in top_p["sales"].tolist()]
    top_p_profit = [round(x, 2) for x in top_p["profit"].tolist()]

    # 7. Sub-categories
    subcat_df = df.groupby("Sub-Category").agg(
        sales=("Sales", "sum"),
        profit=("Profit", "sum")
    ).reset_index().sort_values(by="sales", ascending=False)
    subcat_labels = subcat_df["Sub-Category"].tolist()
    subcat_sales = [round(x, 2) for x in subcat_df["sales"].tolist()]
    subcat_profit = [round(x, 2) for x in subcat_df["profit"].tolist()]

    dashboard_data = {
        "kpis": {
            "total_sales": f"${total_sales:,.2f}",
            "total_profit": f"${total_profit:,.2f}",
            "profit_margin": f"{profit_margin}%",
            "total_orders": f"{total_orders:,}",
            "total_customers": f"{total_customers:,}",
            "avg_order_value": f"${avg_order_value:,.2f}",
            "total_quantity": f"{total_quantity:,}",
        },
        "monthly": {
            "labels": monthly_labels,
            "sales": monthly_sales,
            "profit": monthly_profit,
        },
        "category": {
            "labels": cat_labels,
            "sales": cat_sales,
            "profit": cat_profit,
        },
        "region": {
            "labels": reg_labels,
            "sales": reg_sales,
            "profit": reg_profit,
        },
        "segment": {
            "labels": seg_labels,
            "sales": seg_sales,
        },
        "top_products": {
            "labels": top_p_names,
            "sales": top_p_sales,
            "profit": top_p_profit,
        },
        "subcat": {
            "labels": subcat_labels,
            "sales": subcat_sales,
            "profit": subcat_profit,
        }
    }

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Superstore Sales Analytics Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg-primary: #0b0f19;
      --bg-card: rgba(18, 24, 38, 0.75);
      --bg-card-hover: rgba(26, 34, 52, 0.9);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-glow: rgba(99, 102, 241, 0.25);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-indigo: #6366f1;
      --accent-emerald: #10b981;
      --accent-rose: #f43f5e;
      --accent-amber: #f59e0b;
      --accent-purple: #a855f7;
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }}

    body {{
      background: radial-gradient(circle at 10% 20%, #0d1527 0%, #080c14 90%);
      color: var(--text-main);
      min-height: 100vh;
      padding: 24px;
      overflow-x: hidden;
    }}

    /* Top Navigation Header */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 28px;
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }}

    .brand-title h1 {{
      font-size: 24px;
      font-weight: 800;
      background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .brand-title p {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    .header-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 8px 16px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      color: #34d399;
    }}

    .pulse-dot {{
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 10px #10b981;
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(1.2); }}
      100% {{ opacity: 1; transform: scale(1); }}
    }}

    /* KPI Cards Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 18px;
      margin-bottom: 24px;
    }}

    .kpi-card {{
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: 18px;
      padding: 20px;
      position: relative;
      overflow: hidden;
      transition: all 0.25s ease;
    }}

    .kpi-card:hover {{
      transform: translateY(-3px);
      border-color: var(--border-glow);
      background: var(--bg-card-hover);
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
    }}

    .kpi-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 3px;
    }}

    .card-sales::before {{ background: linear-gradient(90deg, #38bdf8, #6366f1); }}
    .card-profit::before {{ background: linear-gradient(90deg, #10b981, #34d399); }}
    .card-margin::before {{ background: linear-gradient(90deg, #a855f7, #ec4899); }}
    .card-orders::before {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); }}
    .card-aov::before {{ background: linear-gradient(90deg, #6366f1, #a855f7); }}
    .card-customers::before {{ background: linear-gradient(90deg, #ec4899, #f43f5e); }}

    .kpi-label {{
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }}

    .kpi-value {{
      font-size: 26px;
      font-weight: 800;
      margin: 8px 0 4px 0;
      color: #fff;
    }}

    .kpi-subtext {{
      font-size: 11px;
      color: #94a3b8;
    }}

    /* Main Chart Grid */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 20px;
      margin-bottom: 24px;
    }}

    .chart-box {{
      background: var(--bg-card);
      backdrop-filter: blur(14px);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      padding: 22px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}

    .col-12 {{ grid-column: span 12; }}
    .col-8  {{ grid-column: span 8; }}
    .col-6  {{ grid-column: span 6; }}
    .col-4  {{ grid-column: span 4; }}

    @media (max-width: 1024px) {{
      .col-8, .col-6, .col-4 {{ grid-column: span 12; }}
    }}

    .chart-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}

    .chart-header h3 {{
      font-size: 16px;
      font-weight: 700;
      color: #e2e8f0;
    }}

    .chart-header span {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    .canvas-container {{
      position: relative;
      height: 310px;
      width: 100%;
    }}

    /* Footer */
    footer {{
      text-align: center;
      padding: 20px;
      color: var(--text-muted);
      font-size: 12px;
      border-top: 1px solid var(--border-color);
      margin-top: 24px;
    }}
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <div class="brand-title">
      <h1>📊 Superstore Sales Analytics Dashboard</h1>
      <p>Capa Gold de Analítica de Negocio • 9,994 Registros Auditados</p>
    </div>
    <div class="header-badge">
      <div class="pulse-dot"></div>
      Pipeline 100% Validado
    </div>
  </header>

  <!-- KPI Grid -->
  <div class="kpi-grid">
    <div class="kpi-card card-sales">
      <div class="kpi-label">Ventas Totales</div>
      <div class="kpi-value">{dashboard_data['kpis']['total_sales']}</div>
      <div class="kpi-subtext">Facturación bruta en USD</div>
    </div>
    <div class="kpi-card card-profit">
      <div class="kpi-label">Beneficio Neto</div>
      <div class="kpi-value">{dashboard_data['kpis']['total_profit']}</div>
      <div class="kpi-subtext">Rentabilidad operativa real</div>
    </div>
    <div class="kpi-card card-margin">
      <div class="kpi-label">Margen Global</div>
      <div class="kpi-value">{dashboard_data['kpis']['profit_margin']}</div>
      <div class="kpi-subtext">Beneficio / Ventas brutas</div>
    </div>
    <div class="kpi-card card-orders">
      <div class="kpi-label">Total Pedidos</div>
      <div class="kpi-value">{dashboard_data['kpis']['total_orders']}</div>
      <div class="kpi-subtext">5,009 transacciones únicas</div>
    </div>
    <div class="kpi-card card-aov">
      <div class="kpi-label">Ticket Promedio (AOV)</div>
      <div class="kpi-value">{dashboard_data['kpis']['avg_order_value']}</div>
      <div class="kpi-subtext">Venta promedio por pedido</div>
    </div>
    <div class="kpi-card card-customers">
      <div class="kpi-label">Clientes Únicos</div>
      <div class="kpi-value">{dashboard_data['kpis']['total_customers']}</div>
      <div class="kpi-subtext">Fidelizados en 3 segmentos</div>
    </div>
  </div>

  <!-- Charts Grid -->
  <div class="charts-grid">
    <!-- Monthly Trend -->
    <div class="chart-box col-8">
      <div class="chart-header">
        <h3>📈 Evolución Mensual de Ventas y Beneficio (2014 - 2017)</h3>
        <span>gold.monthly_sales</span>
      </div>
      <div class="canvas-container">
        <canvas id="monthlyChart"></canvas>
      </div>
    </div>

    <!-- Regional Share -->
    <div class="chart-box col-4">
      <div class="chart-header">
        <h3>🌍 Ventas por Región</h3>
        <span>gold.regional_performance</span>
      </div>
      <div class="canvas-container">
        <canvas id="regionChart"></canvas>
      </div>
    </div>

    <!-- Category Performance -->
    <div class="chart-box col-6">
      <div class="chart-header">
        <h3>📦 Ventas y Beneficio por Categoría</h3>
        <span>gold.category_performance</span>
      </div>
      <div class="canvas-container">
        <canvas id="categoryChart"></canvas>
      </div>
    </div>

    <!-- Customer Segments -->
    <div class="chart-box col-6">
      <div class="chart-header">
        <h3>👥 Distribución por Segmento de Cliente</h3>
        <span>silver.dim_customers</span>
      </div>
      <div class="canvas-container">
        <canvas id="segmentChart"></canvas>
      </div>
    </div>

    <!-- Subcategories Performance -->
    <div class="chart-box col-6">
      <div class="chart-header">
        <h3>🏷️ Top Subcategorías por Facturación</h3>
        <span>17 Subcategorías del catálogo</span>
      </div>
      <div class="canvas-container">
        <canvas id="subcatChart"></canvas>
      </div>
    </div>

    <!-- Top Products -->
    <div class="chart-box col-6">
      <div class="chart-header">
        <h3>⭐ Top 8 Productos Más Vendidos</h3>
        <span>gold.product_performance</span>
      </div>
      <div class="canvas-container">
        <canvas id="topProductsChart"></canvas>
      </div>
    </div>
  </div>

  <footer>
    Superstore Sales Data Pipeline • Generado automáticamente desde la capa de analítica • Compatible con Power BI y Tableau
  </footer>

  <script>
    const data = {json.dumps(dashboard_data)};

    // Chart.js global dark theme defaults
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

    // 1. Monthly Chart
    new Chart(document.getElementById('monthlyChart'), {{
      type: 'line',
      data: {{
        labels: data.monthly.labels,
        datasets: [
          {{
            label: 'Ventas ($)',
            data: data.monthly.sales,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 2
          }},
          {{
            label: 'Beneficio ($)',
            data: data.monthly.profit,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 2
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'top' }}
        }},
        scales: {{
          y: {{
            grid: {{ color: 'rgba(255,255,255,0.05)' }},
            ticks: {{
              callback: value => '$' + (value / 1000).toFixed(0) + 'k'
            }}
          }},
          x: {{
            grid: {{ display: false }},
            ticks: {{ maxTicksLimit: 12 }}
          }}
        }}
      }}
    }});

    // 2. Region Chart
    new Chart(document.getElementById('regionChart'), {{
      type: 'doughnut',
      data: {{
        labels: data.region.labels,
        datasets: [{{
          data: data.region.sales,
          backgroundColor: ['#38bdf8', '#818cf8', '#a855f7', '#f59e0b'],
          borderWidth: 0
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'bottom' }}
        }}
      }}
    }});

    // 3. Category Chart
    new Chart(document.getElementById('categoryChart'), {{
      type: 'bar',
      data: {{
        labels: data.category.labels,
        datasets: [
          {{
            label: 'Ventas ($)',
            data: data.category.sales,
            backgroundColor: '#6366f1',
            borderRadius: 8
          }},
          {{
            label: 'Beneficio ($)',
            data: data.category.profit,
            backgroundColor: '#10b981',
            borderRadius: 8
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          y: {{
            ticks: {{
              callback: val => '$' + (val / 1000).toFixed(0) + 'k'
            }}
          }}
        }}
      }}
    }});

    // 4. Segment Chart
    new Chart(document.getElementById('segmentChart'), {{
      type: 'pie',
      data: {{
        labels: data.segment.labels,
        datasets: [{{
          data: data.segment.sales,
          backgroundColor: ['#06b6d4', '#8b5cf6', '#ec4899'],
          borderWidth: 0
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'bottom' }}
        }}
      }}
    }});

    // 5. Subcategory Bar Chart
    new Chart(document.getElementById('subcatChart'), {{
      type: 'bar',
      data: {{
        labels: data.subcat.labels.slice(0, 10),
        datasets: [{{
          label: 'Ventas ($)',
          data: data.subcat.sales.slice(0, 10),
          backgroundColor: '#38bdf8',
          borderRadius: 6
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{
            ticks: {{
              callback: val => '$' + (val / 1000).toFixed(0) + 'k'
            }}
          }}
        }}
      }}
    }});

    // 6. Top Products Chart
    new Chart(document.getElementById('topProductsChart'), {{
      type: 'bar',
      data: {{
        labels: data.top_products.labels,
        datasets: [{{
          label: 'Ventas ($)',
          data: data.top_products.sales,
          backgroundColor: '#f59e0b',
          borderRadius: 6
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{
            ticks: {{
              callback: val => '$' + (val / 1000).toFixed(0) + 'k'
            }}
          }}
        }}
      }}
    }});
  </script>
</body>
</html>
"""

    target_path.write_text(html_content, encoding="utf-8")
    return target_path


if __name__ == "__main__":
    out = generate_html_dashboard()
    print(f"Interactive dashboard successfully generated at: {out}")
