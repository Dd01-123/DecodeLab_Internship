# Unified E-Commerce Analytics Pipeline

This backend runs an end-to-end analytics workflow for e-commerce order data:

1. Phase 1: Data Cleaning and Data Preparation
2. Phase 2: Exploratory Data Analysis and Visualizations
3. Phase 3: Data Visualization and Storytelling
4. Phase 4: SQL Analytics and Executive Business Reporting

The single entry point is:

```bash
python -m app.main
```

## Project Structure

```text
application/backend/
|-- app/
|   |-- cleaning/          # Data loading, cleaning, validation, quality reporting
|   |-- core/              # Unified orchestration and execution context
|   |-- eda/               # Profiling, statistics, visualizations, EDA insights
|   |-- visualization/     # Business visuals, dashboard, storytelling reports
|   `-- sql_analytics/     # SQLite loading, SQL execution, SQL reports
|-- data/
|   |-- raw/
|   `-- processed/
|-- reports/
|   |-- eda/
|   `-- sql_insights/
|-- sql/                   # Reusable named SQL query library
|-- visualizations/
`-- logs/
```

## Pipeline Flow

Running `python -m app.main` executes:

1. Load raw dataset from `data/raw/ecommerce_raw.xlsx`
2. Clean and validate records
3. Save cleaned dataset to `data/processed/ecommerce_cleaned.csv`
4. Run EDA and generate visualizations
5. Run the visualization storytelling framework
6. Generate revenue, customer, trend, categorical, distribution, correlation, and outlier charts
7. Generate `visualizations/dashboards/executive_dashboard.png`
8. Generate visualization narrative reports
9. Load cleaned data into SQLite at `data/processed/analytics.db`
10. Create the `ecommerce_orders` table
11. Run SQL analytics from the reusable query files in `sql/`
12. Generate SQL insight reports
13. Generate `reports/sql_insights/executive_business_report.txt`
14. Generate `reports/final_pipeline_report.txt`

## Visualization Storytelling Coverage

The visualization phase generates:

- Distribution charts
- Outlier charts
- Correlation heatmaps
- Categorical charts
- Revenue charts
- Customer charts
- Trend charts
- Executive dashboard image
- Storytelling report
- Executive visual summary

## SQL Analytics Coverage

The Phase 3 SQL layer generates reports for:

- KPI summary
- Customer insights
- Product insights
- Revenue insights
- Order insights
- Payment insights
- Referral insights
- Trend insights
- Executive business recommendations

Reusable SQL files live in `sql/`:

```text
kpis.sql
customer_analysis.sql
product_analysis.sql
revenue_analysis.sql
order_analysis.sql
payment_analysis.sql
referral_analysis.sql
trend_analysis.sql
```

Each SQL file uses named query blocks such as `-- name: total_orders`, which allows Python to execute and label report sections automatically.

## Outputs

Key generated outputs include:

- `data/processed/ecommerce_cleaned.csv`
- `data/processed/analytics.db`
- `reports/data_quality_report.txt`
- `reports/cleaning_summary.txt`
- `reports/eda/*`
- `reports/visualization/visualization_summary.txt`
- `reports/visualization/storytelling_report.txt`
- `reports/visualization/executive_visual_summary.txt`
- `visualizations/dashboards/executive_dashboard.png`
- `reports/sql_insights/kpi_report.txt`
- `reports/sql_insights/customer_insights.txt`
- `reports/sql_insights/product_insights.txt`
- `reports/sql_insights/revenue_insights.txt`
- `reports/sql_insights/order_insights.txt`
- `reports/sql_insights/payment_insights.txt`
- `reports/sql_insights/referral_insights.txt`
- `reports/sql_insights/trend_insights.txt`
- `reports/sql_insights/executive_business_report.txt`
- `reports/final_pipeline_report.txt`

## Custom Execution

```bash
python -m app.main --input data/raw/ecommerce_raw.xlsx
python -m app.main --output data/processed/custom_cleaned.csv
python -m app.main --verbose
```

The SQL analytics phase always reuses the cleaned dataset produced by the cleaning phase in the same run.
