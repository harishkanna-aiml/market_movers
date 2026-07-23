# market_movers

A production-oriented Python collector that retrieves US stock market movers from multiple sources in parallel and exports a professionally formatted Excel workbook.

## Included integrations

- **Financial Modeling Prep (FMP):** gainers, losers, and most active stocks.
- **Polygon.io:** gainers and losers snapshot endpoints.
- **Yahoo Finance:** gainers, losers, and most-active predefined screeners through `yfinance`.
- **Finviz:** public screener pages for gainers, losers, and most active stocks.
- **Robinhood:** safe placeholder module. It creates the required sheets but intentionally returns no data because Robinhood does not provide a supported public market-movers API for this use case.

## Workbook sheets

`Robinhood_Gainers`, `Robinhood_Losers`, `Robinhood_Actives`, `FMP_Gainers`, `FMP_Losers`, `FMP_Actives`, `Polygon_Gainers`, `Polygon_Losers`, `Yahoo_Market`, `Finviz_Market`, and `Summary`.

The workbook includes frozen headers, filters, striped tables, automatic column widths, number formatting, and a red-yellow-green conditional color scale for **Change %**. The **Summary** sheet combines all available records and sorts them by **Change %** descending.

## Setup

### 1. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

On Windows, copy `.env.example` to `.env` manually. Add your FMP and Polygon API keys. Yahoo and Finviz do not require keys, though access and data availability are controlled by their respective providers.

### 4. Run

```bash
python main.py
```

The generated workbook is saved under `output/` and logs are written to `logs/market_movers.log`.

Custom output file and row limit:

```bash
python main.py --output output/today.xlsx --limit 100
```

## Reliability behavior

- All source jobs execute concurrently with `ThreadPoolExecutor`.
- HTTP calls use connection pooling and exponential-backoff retries for transient status codes such as 429 and 5xx.
- A failure in one source does not stop the workbook from being generated; its sheet remains present with headers and the error is logged.
- API keys are read only from `.env`/environment variables and are never embedded in source code.

## Important notes

- Market data may be delayed, incomplete, rate-limited, or restricted by your subscription plan.
- `yfinance` is an independent open-source package and is not affiliated with Yahoo. Use it in accordance with Yahoo's terms.
- Finviz scraping depends on its HTML structure and may require maintenance if the site changes. Keep request volume low and comply with its terms and robots policies.
- The Robinhood module is deliberately a placeholder. Do not bypass authentication or platform controls. Replace it only with an approved integration.
- This project is for data engineering/research and is not financial advice.

## Project structure

```text
market_movers/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── apis/
│   ├── __init__.py
│   ├── fmp.py
│   ├── polygon.py
│   ├── yahoo.py
│   ├── finviz.py
│   └── robinhood.py
├── utils/
│   ├── __init__.py
│   ├── excel_writer.py
│   ├── logger.py
│   └── helpers.py
├── output/
│   └── .gitkeep
└── logs/
    └── .gitkeep
```
