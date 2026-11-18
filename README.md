# Online Retail Data Cleaning & Preparation

**Task 1 | Data Cleaning & Preparation | Data Analyst Portfolio Project**

A reproducible Python/Pandas data-cleaning project using the **Online Retail** dataset from the UCI Machine Learning Repository. The project checks data quality, standardizes text, corrects data types, removes exact duplicate rows, handles unusable records, preserves returns/cancellations with flags, and exports a cleaned dataset with an audit report.

## 1. Project objective

Prepare raw retail transaction data for reliable analysis by identifying missing values, duplicate records, inconsistent text, invalid values, and incorrect data types. The output is a clean transaction-level CSV plus a machine-readable data-quality report.

## 2. Dataset

- **Name:** Online Retail
- **Publisher:** UCI Machine Learning Repository
- **Dataset ID:** 352
- **Coverage:** 1 December 2010 to 9 December 2011
- **Publisher-reported size:** 541,909 instances and 8 variables
- **License:** CC BY 4.0
- **Official source:** https://archive.ics.uci.edu/dataset/352/online+retail
- **Citation:** Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33.

The repository does not include the raw workbook because it is a large source file. Download `Online Retail.xlsx` from the official UCI page and save it as `data/raw/Online Retail.xlsx`, or use the automated UCI fetch command below.

## 3. Tools and skills

- Python 3
- Pandas and NumPy
- Excel-compatible CSV output
- Data profiling, missing-value analysis, duplicate handling, type conversion, text standardization, validation, reproducible scripting, Git/GitHub

## 4. Repository structure

```text
online-retail-data-cleaning/
├── data/
│   ├── raw/                 # Put original UCI workbook here (not committed)
│   └── processed/           # Cleaned CSV is generated here (not committed)
├── reports/                # Quality reports are generated here
├── src/
│   └── clean_data.py        # End-to-end cleaning script
├── .gitignore
├── requirements.txt
└── README.md
```

## 5. Setup and run

### Option A — Download the dataset manually

1. Open the [official UCI dataset page](https://archive.ics.uci.edu/dataset/352/online+retail).
2. Download `Online Retail.xlsx`.
3. Place it at `data/raw/Online Retail.xlsx`.
4. Run:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python src/clean_data.py --input "data/raw/Online Retail.xlsx"
```

### Option B — Fetch through the UCI repository package

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
python src/clean_data.py --fetch-uci
```

## 6. Data-cleaning steps

| Area | Check / action | Decision |
|---|---|---|
| Column names | Trim header whitespace and validate expected columns | Keep the eight documented fields |
| Text consistency | Trim whitespace, collapse repeated spaces, standardize case | Invoice/product codes uppercase; descriptions uppercase; country title case |
| Data types | Convert quantity, price, customer ID and invoice date | Quantity integer; price numeric; customer ID kept as nullable text; date as datetime |
| Duplicates | Detect exact duplicate rows | Remove exact duplicates only |
| Missing essential data | Check invoice, product, description, quantity, date, price and country | Remove rows missing fields required for transaction analysis |
| Missing CustomerID | Check missing customer identifiers | Keep as missing; do not invent customer identities or impute IDs |
| Invalid values | Coerce unparseable numeric/date values to missing, then apply essential-field rule | Exclude rows with invalid essential fields and record counts |
| Returns/cancellations | Detect invoice numbers beginning with C and negative quantities | Retain and flag; do not silently discard legitimate return/cancellation records |
| Derived field | Calculate quantity × unit price | Add `LineTotal` |

**Important:** The script generates the actual counts from the downloaded source file. Do not put assumed cleaning counts in your submission. The UCI dataset page describes the source and fields; the audit report records what happened in your local run.

## 7. Output files

After running the script, you will get:

- `data/processed/online_retail_cleaned.csv` — cleaned transaction-level dataset.
- `reports/data_quality_report.json` — before/after row counts, missing-value profile, data types and cleaning-action counts.
- `reports/missing_values_after_cleaning.csv` — remaining missing-value counts and percentages by column.

These generated files are ignored by Git by default because the cleaned transaction CSV can be large. If your reviewer needs the actual output, upload it to Google Drive or GitHub Releases and add its share link to this README. You may also commit the reports if they are small by removing the relevant report patterns from `.gitignore`.

## 8. Validation checklist

After execution, verify:

- [ ] The script completes without errors.
- [ ] The cleaned CSV opens in Excel.
- [ ] `InvoiceDate` is parseable as a date/time column.
- [ ] `Quantity` is integer and `UnitPrice` is numeric.
- [ ] Exact duplicate rows were removed.
- [ ] Missing CustomerID values are retained and documented.
- [ ] Cancellation/return rows are flagged, not silently deleted.
- [ ] The JSON report's output row count matches the CSV row count.

## 9. Business value

Reliable cleaning reduces errors in sales summaries, product performance reporting, customer analysis and time-based reporting. Retaining and flagging cancellations/returns also avoids overstating sales by making those records identifiable for later business rules.

## 10. Limitations and assumptions

- Exact duplicate rows are treated as accidental duplicates; repeated invoice/product lines with different values are not automatically removed.
- Missing CustomerID is not imputed because customer identity cannot be inferred safely.
- Cancellation and negative-quantity records are retained for traceability. A separate net-sales analysis should define how returns and cancellations affect revenue.
- The `LineTotal` field is a line-level arithmetic amount, not a complete accounting measure including taxes, shipping or discounts.

## 11. Author

**Om Jadhav**  
Data Analytics | Python | SQL | Excel

## 12. Dataset attribution

Dataset provided by Daqing Chen via the UCI Machine Learning Repository, licensed under CC BY 4.0. Please retain this attribution when redistributing or adapting the dataset.
